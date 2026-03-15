import asyncio
import logging

from aiogram.types import BufferedInputFile

from src.config import settings
from src.db.repository import ChatRepository, ChatSettingsRepository
from src.services.export import build_chat_export
from src.services.openrouter import OpenRouterClient, OpenRouterRequestOptions

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = "Summarize the conversation state for future turns."
MODE_INSTRUCTIONS = {
    "chat": "",
    "summarize": "Current mode: summarize. Prefer concise summaries, key points, decisions, and action items.",
    "translate": "Current mode: translate. Translate faithfully, preserve tone, and keep the output natural and useful.",
    "analyze": "Current mode: analyze. Focus on structure, risks, evidence, conclusions, and practical recommendations.",
}


class ChatService:
    def __init__(
        self,
        repository: ChatRepository,
        ai_client: OpenRouterClient,
        settings_repository: ChatSettingsRepository | None = None,
    ) -> None:
        self._repository = repository
        self._ai_client = ai_client
        self._settings_repository = settings_repository

    async def build_context_messages(self, chat_id: int) -> list[dict[str, object]]:
        chat_settings_task = None
        if self._settings_repository is not None:
            chat_settings_task = asyncio.to_thread(self._settings_repository.get_chat_settings, chat_id)

        recent_history_task = asyncio.to_thread(
            self._repository.get_recent_messages,
            chat_id,
            settings.recent_messages_limit,
        )
        summary_record_task = asyncio.to_thread(self._repository.get_chat_summary, chat_id)

        chat_settings = await chat_settings_task if chat_settings_task is not None else None
        recent_history, summary_record = await asyncio.gather(recent_history_task, summary_record_task)

        system_prompt = settings.system_prompt
        if chat_settings is not None and chat_settings.system_prompt_override:
            system_prompt = chat_settings.system_prompt_override

        messages: list[dict[str, object]] = [{"role": "system", "content": system_prompt}]
        mode = chat_settings.mode if chat_settings is not None and getattr(chat_settings, "mode", "") else "chat"
        mode_instruction = MODE_INSTRUCTIONS.get(mode, "")
        if mode_instruction:
            messages.append({"role": "system", "content": mode_instruction})

        memory_enabled = chat_settings is None or bool(chat_settings.memory_enabled)
        if memory_enabled and summary_record is not None and summary_record.summary_text.strip():
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Conversation summary from earlier turns. Use it as memory, "
                        "but prioritize newer user instructions if they conflict.\n\n"
                        f"{summary_record.summary_text}"
                    ),
                }
            )

        for item in recent_history:
            if item.role in {"user", "assistant"}:
                messages.append({"role": item.role, "content": item.content})
        return messages

    async def handle_text_message(self, chat_id: int, user_id: int, text: str) -> dict[str, str | int | float | None]:
        return await self.handle_user_request(
            chat_id=chat_id,
            user_id=user_id,
            user_log_content=text,
            user_content=text,
        )

    async def handle_user_request(
        self,
        chat_id: int,
        user_id: int,
        user_log_content: str,
        user_content: str | list[dict[str, object]],
    ) -> dict[str, str | int | float | None]:
        context = await self.build_context_messages(chat_id)
        context.append({"role": "user", "content": user_content})

        request_options = await self._build_request_options(chat_id, user_content)
        response = await self._ai_client.generate_response(context, request_options=request_options)
        answer = str(response["content"])
        prompt_tokens = self._to_int(response.get("prompt_tokens"))
        completion_tokens = self._to_int(response.get("completion_tokens"))
        total_tokens = self._to_int(response.get("total_tokens"))
        cost = self._to_float(response.get("cost"))

        await asyncio.gather(
            asyncio.to_thread(
                self._repository.add_message,
                chat_id,
                user_id,
                "user",
                user_log_content,
            ),
            asyncio.to_thread(
                self._repository.add_message,
                chat_id,
                user_id,
                "assistant",
                answer,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
            ),
        )

        await self._refresh_summary_if_needed(chat_id)

        logger.info(
            "OpenRouter usage | chat_id=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s cost=%s",
            chat_id,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost,
        )

        return {
            "content": answer,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
        }

    async def get_usage_summary(self, chat_id: int) -> dict[str, float | int]:
        return await asyncio.to_thread(self._repository.get_chat_usage_summary, chat_id)

    async def get_last_request_usage(self, chat_id: int) -> dict[str, float | int] | None:
        record = await asyncio.to_thread(self._repository.get_last_assistant_message, chat_id)
        if record is None:
            return None
        return {
            "prompt_tokens": record.prompt_tokens or 0,
            "completion_tokens": record.completion_tokens or 0,
            "total_tokens": record.total_tokens or 0,
            "cost": float(record.cost or 0.0),
        }

    async def get_chat_mode(self, chat_id: int) -> str:
        if self._settings_repository is None:
            return "chat"
        settings_record = await asyncio.to_thread(self._settings_repository.get_chat_settings, chat_id)
        if settings_record is None or not getattr(settings_record, "mode", ""):
            return "chat"
        return settings_record.mode

    async def set_chat_mode(self, chat_id: int, mode: str) -> None:
        if self._settings_repository is None:
            return
        await asyncio.to_thread(
            self._settings_repository.upsert_chat_settings,
            chat_id=chat_id,
            mode=mode,
        )

    async def clear_chat(self, chat_id: int) -> int:
        return await asyncio.to_thread(self._repository.clear_chat, chat_id)

    async def export_chat(self, chat_id: int) -> BufferedInputFile | None:
        messages = await asyncio.to_thread(self._repository.get_all_messages, chat_id)
        if not messages:
            return None

        content = build_chat_export(chat_id, messages).encode("utf-8")
        return BufferedInputFile(content, filename=f"chat_{chat_id}_export.txt")

    async def _refresh_summary_if_needed(self, chat_id: int) -> None:
        chat_settings = None
        if self._settings_repository is not None:
            chat_settings = await asyncio.to_thread(self._settings_repository.get_chat_settings, chat_id)
        if chat_settings is not None and not bool(chat_settings.memory_enabled):
            return

        summary_record = await asyncio.to_thread(self._repository.get_chat_summary, chat_id)
        last_compacted_message_id = summary_record.last_compacted_message_id if summary_record is not None else 0
        pending_messages = await asyncio.to_thread(
            self._repository.get_messages_after,
            chat_id,
            last_compacted_message_id,
        )

        if len(pending_messages) < settings.summary_update_min_messages:
            return

        summary_input = self._build_summary_source_text(summary_record.summary_text if summary_record else "", pending_messages)
        summary_messages = [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Produce a concise rolling summary of the conversation. Preserve user preferences, "
                    "constraints, ongoing tasks, decisions, and promised follow-ups. Omit filler.\n\n"
                    f"{summary_input}"
                ),
            },
        ]
        summary_response = await self._ai_client.generate_response(
            summary_messages,
            request_options=OpenRouterRequestOptions(
                primary_model=settings.openrouter_summary_model or settings.openrouter_model,
                fallback_models=self._default_fallback_models(),
                temperature=0.2,
                max_tokens=min(settings.model_max_tokens, 1200),
                route_name="conversation_summary",
            ),
        )
        summary_text = str(summary_response["content"]).strip()
        if not summary_text:
            return

        if len(summary_text) > settings.summary_max_chars:
            summary_text = summary_text[: settings.summary_max_chars].rstrip()

        await asyncio.to_thread(
            self._repository.upsert_chat_summary,
            chat_id,
            summary_text,
            pending_messages[-1].id,
        )

    async def _build_request_options(
        self,
        chat_id: int,
        user_content: str | list[dict[str, object]],
    ) -> OpenRouterRequestOptions:
        chat_settings = None
        if self._settings_repository is not None:
            chat_settings = await asyncio.to_thread(self._settings_repository.get_chat_settings, chat_id)

        mode = chat_settings.mode if chat_settings is not None and getattr(chat_settings, "mode", "") else "chat"
        primary_model = self._select_primary_model(mode=mode, user_content=user_content)
        max_tokens_override = getattr(chat_settings, "max_tokens_override", None) if chat_settings is not None else None
        max_tokens = max_tokens_override if max_tokens_override else settings.model_max_tokens
        temperature = (
            getattr(chat_settings, "temperature_override", None)
            if chat_settings is not None and getattr(chat_settings, "temperature_override", None) is not None
            else settings.model_temperature
        )
        return OpenRouterRequestOptions(
            primary_model=primary_model,
            fallback_models=self._default_fallback_models(primary_model),
            temperature=temperature,
            max_tokens=max_tokens,
            route_name=f"chat:{mode}",
        )

    def _select_primary_model(self, *, mode: str, user_content: str | list[dict[str, object]]) -> str:
        if isinstance(user_content, list):
            return settings.openrouter_vision_model or settings.openrouter_analyze_model or settings.openrouter_model
        if mode == "summarize" and settings.openrouter_summary_model:
            return settings.openrouter_summary_model
        if mode == "translate" and settings.openrouter_translate_model:
            return settings.openrouter_translate_model
        if mode == "analyze" and settings.openrouter_analyze_model:
            return settings.openrouter_analyze_model
        return settings.openrouter_model

    def _default_fallback_models(self, primary_model: str | None = None) -> list[str]:
        fallbacks: list[str] = []
        if settings.openrouter_fallback_model:
            fallbacks.append(settings.openrouter_fallback_model)
        if primary_model is not None and primary_model != settings.openrouter_model:
            fallbacks.append(settings.openrouter_model)
        return fallbacks

    @staticmethod
    def _build_summary_source_text(previous_summary: str, messages: list[object]) -> str:
        lines: list[str] = []
        if previous_summary.strip():
            lines.append("Previous summary:")
            lines.append(previous_summary.strip())
            lines.append("")

        lines.append("New messages to merge:")
        for item in messages:
            if getattr(item, "role", "") not in {"user", "assistant"}:
                continue
            role = str(getattr(item, "role", "")).upper()
            content = str(getattr(item, "content", "")).strip()
            if not content:
                continue
            lines.append(f"{role}: {content}")

        combined = "\n".join(lines).strip()
        if len(combined) <= settings.summary_source_max_chars:
            return combined
        return combined[-settings.summary_source_max_chars :]

    @staticmethod
    def _to_int(value: object) -> int | None:
        if value is None:
            return None
        return int(value)

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        return float(value)
