import logging
from collections.abc import Sequence

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from src.bot.messages import (
    AUDIO_HANDLER_ERROR,
    CLEAR_RESULT_TEMPLATE,
    EMPTY_EXPORT_TEXT,
    EMPTY_MESSAGE_TEXT,
    FILE_HANDLER_ERROR,
    HELP_TEXT,
    IMAGE_HANDLER_ERROR,
    LONG_RESPONSE_CAPTION,
    NO_USAGE_TEXT,
    START_TEXT,
    TEXT_HANDLER_ERROR,
    VOICE_HANDLER_ERROR,
    build_status_text,
    build_usage_text,
)
from src.config import settings
from src.services.access import is_allowed_message
from src.services.chat_service import ChatService
from src.services.content import (
    ContentExtractionError,
    ExtractedImage,
    ensure_supported_file_size,
    extract_document,
    extract_image,
)
from src.services.openrouter import OpenRouterError
from src.services.speech import SpeechToTextError, SpeechToTextService
from src.utils.responses import FormattedTextChunk, build_response_payloads
from src.utils.telegram_files import download_telegram_file
from src.utils.text import ensure_text

logger = logging.getLogger(__name__)

router = Router()


def build_router(chat_service: ChatService, speech_service: SpeechToTextService) -> Router:
    @router.message(Command("start"))
    async def start_handler(message: Message) -> None:
        if not _is_allowed(message):
            return
        await message.answer(START_TEXT)

    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        if not _is_allowed(message):
            return
        await message.answer(HELP_TEXT)

    @router.message(Command("status"))
    async def status_handler(message: Message) -> None:
        if not _is_allowed(message):
            return
        await message.answer(
            build_status_text(
                model=settings.openrouter_model,
                context_limit=settings.context_messages_limit,
                max_tokens=settings.model_max_tokens,
                temperature=settings.model_temperature,
                max_file_size_mb=settings.max_file_size_mb,
                max_extracted_text_chars=settings.max_extracted_text_chars,
                whisper_model_size=settings.whisper_model_size,
                max_audio_duration_seconds=settings.max_audio_duration_seconds,
            )
        )

    @router.message(Command("usage"))
    async def usage_handler(message: Message) -> None:
        if not _is_allowed(message):
            return

        last_usage = chat_service.get_last_request_usage(message.chat.id)
        summary = chat_service.get_usage_summary(message.chat.id)

        if last_usage is None:
            await message.answer(NO_USAGE_TEXT)
            return

        await message.answer(build_usage_text(last_usage, summary))

    @router.message(Command("clear"))
    async def clear_handler(message: Message) -> None:
        if not _is_allowed(message):
            return
        deleted = chat_service.clear_chat(message.chat.id)
        await message.answer(CLEAR_RESULT_TEMPLATE.format(deleted=deleted))

    @router.message(Command("export"))
    async def export_handler(message: Message) -> None:
        if not _is_allowed(message):
            return
        export_file = chat_service.export_chat(message.chat.id)
        if export_file is None:
            await message.answer(EMPTY_EXPORT_TEXT)
            return
        await message.answer_document(export_file, caption="Экспорт истории чата.")

    @router.message(F.voice)
    async def voice_handler(message: Message) -> None:
        if not _is_allowed(message) or message.voice is None or message.from_user is None:
            return

        await _show_typing(message)
        try:
            ensure_supported_file_size(message.voice.file_size)
            file_bytes, _mime_type = await download_telegram_file(message.bot, message.voice.file_id)
            transcribed = speech_service.transcribe(
                file_name=f"voice_{message.voice.file_unique_id}.ogg",
                data=file_bytes,
                user_text=ensure_text(message.caption),
                duration_seconds=message.voice.duration,
            )
            result = await chat_service.handle_user_request(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                user_log_content=transcribed.log_content,
                user_content=transcribed.model_text,
            )
        except (SpeechToTextError, ContentExtractionError) as exc:
            await message.answer(str(exc))
            return
        except OpenRouterError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while handling a voice message")
            await message.answer(VOICE_HANDLER_ERROR)
            return

        await _send_response(message, str(result["content"]))

    @router.message(F.audio)
    async def audio_handler(message: Message) -> None:
        if not _is_allowed(message) or message.audio is None or message.from_user is None:
            return

        await _show_typing(message)
        try:
            ensure_supported_file_size(message.audio.file_size)
            file_bytes, _mime_type = await download_telegram_file(message.bot, message.audio.file_id)
            source_name = message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3"
            transcribed = speech_service.transcribe(
                file_name=source_name,
                data=file_bytes,
                user_text=ensure_text(message.caption),
                duration_seconds=message.audio.duration,
            )
            result = await chat_service.handle_user_request(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                user_log_content=transcribed.log_content,
                user_content=transcribed.model_text,
            )
        except (SpeechToTextError, ContentExtractionError) as exc:
            await message.answer(str(exc))
            return
        except OpenRouterError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while handling an audio file")
            await message.answer(AUDIO_HANDLER_ERROR)
            return

        await _send_response(message, str(result["content"]))

    @router.message(F.photo)
    async def photo_handler(message: Message) -> None:
        if not _is_allowed(message) or not message.photo or message.from_user is None:
            return

        await _show_typing(message)
        photo = message.photo[-1]
        try:
            ensure_supported_file_size(photo.file_size)
            file_bytes, mime_type = await download_telegram_file(message.bot, photo.file_id)
            extracted = extract_image(
                file_name=f"photo_{photo.file_unique_id}.jpg",
                mime_type=mime_type,
                data=file_bytes,
                user_text=ensure_text(message.caption),
            )
            result = await chat_service.handle_user_request(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                user_log_content=extracted.log_content,
                user_content=_image_prompt_payload(extracted),
            )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except OpenRouterError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while handling a photo")
            await message.answer(IMAGE_HANDLER_ERROR)
            return

        await _send_response(message, str(result["content"]))

    @router.message(F.document)
    async def document_handler(message: Message) -> None:
        if not _is_allowed(message) or message.document is None or message.from_user is None:
            return

        await _show_typing(message)
        try:
            ensure_supported_file_size(message.document.file_size)
            file_bytes, detected_mime_type = await download_telegram_file(message.bot, message.document.file_id)

            if (message.document.mime_type or detected_mime_type or "").startswith("image/"):
                extracted_image = extract_image(
                    file_name=message.document.file_name or "image",
                    mime_type=message.document.mime_type or detected_mime_type,
                    data=file_bytes,
                    user_text=ensure_text(message.caption),
                )
                result = await chat_service.handle_user_request(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    user_log_content=extracted_image.log_content,
                    user_content=_image_prompt_payload(extracted_image),
                )
            else:
                extracted_document = extract_document(
                    file_name=message.document.file_name or "document",
                    data=file_bytes,
                    user_text=ensure_text(message.caption),
                )
                result = await chat_service.handle_user_request(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    user_log_content=extracted_document.log_content,
                    user_content=extracted_document.model_text,
                )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except OpenRouterError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while handling a document")
            await message.answer(FILE_HANDLER_ERROR)
            return

        await _send_response(message, str(result["content"]))

    @router.message(F.text)
    async def text_handler(message: Message) -> None:
        if not _is_allowed(message) or message.from_user is None:
            return

        text = ensure_text(message.text)
        if not text:
            await message.answer(EMPTY_MESSAGE_TEXT)
            return

        await _show_typing(message)
        try:
            result = await chat_service.handle_text_message(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                text=text,
            )
        except OpenRouterError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while handling a text message")
            await message.answer(TEXT_HANDLER_ERROR)
            return

        await _send_response(message, str(result["content"]))

    return router


def _is_allowed(message: Message) -> bool:
    return is_allowed_message(message)


async def _show_typing(message: Message) -> None:
    await message.bot.send_chat_action(message.chat.id, "typing")


def _image_prompt_payload(extracted: ExtractedImage) -> list[dict[str, object]]:
    return [
        {"type": "text", "text": extracted.prompt_text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{extracted.mime_type};base64,{extracted.base64_data}"
            },
        },
    ]


async def _send_response(message: Message, answer: str) -> None:
    payload = build_response_payloads(answer)
    if isinstance(payload, BufferedInputFile):
        await message.answer_document(payload, caption=LONG_RESPONSE_CAPTION)
        return

    await _send_text_chunks(message, payload)


async def _send_text_chunks(message: Message, chunks: Sequence[FormattedTextChunk]) -> None:
    for chunk in chunks:
        try:
            await message.answer(chunk.html_text, parse_mode="HTML")
        except TelegramBadRequest:
            await message.answer(chunk.plain_text, parse_mode=None)
