import logging

from aiogram.types import BufferedInputFile

from src.config import settings
from src.db.repository import ChatRepository
from src.services.export import build_chat_export
from src.services.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, repository: ChatRepository, ai_client: OpenRouterClient) -> None:
        self._repository = repository
        self._ai_client = ai_client

    def build_context_messages(self, chat_id: int) -> list[dict[str, object]]:
        history = self._repository.get_recent_messages(chat_id, settings.context_messages_limit)

        messages: list[dict[str, object]] = [{"role": "system", "content": settings.system_prompt}]
        for item in history:
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
        context = self.build_context_messages(chat_id)
        context.append({"role": "user", "content": user_content})

        response = await self._ai_client.generate_response(context)
        answer = str(response["content"])
        prompt_tokens = self._to_int(response.get("prompt_tokens"))
        completion_tokens = self._to_int(response.get("completion_tokens"))
        total_tokens = self._to_int(response.get("total_tokens"))
        cost = self._to_float(response.get("cost"))

        self._repository.add_message(
            chat_id=chat_id,
            user_id=user_id,
            role="user",
            content=user_log_content,
        )
        self._repository.add_message(
            chat_id=chat_id,
            user_id=user_id,
            role="assistant",
            content=answer,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
        )

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

    def get_usage_summary(self, chat_id: int) -> dict[str, float | int]:
        return self._repository.get_chat_usage_summary(chat_id)

    def get_last_request_usage(self, chat_id: int) -> dict[str, float | int] | None:
        record = self._repository.get_last_assistant_message(chat_id)
        if record is None:
            return None
        return {
            "prompt_tokens": record.prompt_tokens or 0,
            "completion_tokens": record.completion_tokens or 0,
            "total_tokens": record.total_tokens or 0,
            "cost": float(record.cost or 0.0),
        }

    def clear_chat(self, chat_id: int) -> int:
        return self._repository.clear_chat(chat_id)

    def export_chat(self, chat_id: int) -> BufferedInputFile | None:
        messages = self._repository.get_all_messages(chat_id)
        if not messages:
            return None

        content = build_chat_export(chat_id, messages).encode("utf-8")
        return BufferedInputFile(content, filename=f"chat_{chat_id}_export.txt")

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
