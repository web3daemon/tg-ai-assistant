import logging

from aiogram import F, Router
from aiogram.types import Message

from src.bot.common import finish_processing, is_allowed, send_response, show_processing
from src.bot.dependencies import BotDependencies
from src.bot.messages import (
    AUDIO_HANDLER_ERROR,
    BACKGROUND_JOB_ACCEPTED_TEXT,
    EMPTY_MESSAGE_TEXT,
    TEXT_HANDLER_ERROR,
)
from src.services.content import ContentExtractionError
from src.services.openrouter import OpenRouterError
from src.utils.text import ensure_text

logger = logging.getLogger(__name__)


def build_content_router(deps: BotDependencies) -> Router:
    router = Router(name="content")

    @router.message(F.voice)
    async def voice_handler(message: Message) -> None:
        if not is_allowed(message) or message.voice is None or message.from_user is None:
            return

        try:
            job = await deps.background_job_service.enqueue_voice(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                file_id=message.voice.file_id,
                file_unique_id=message.voice.file_unique_id,
                caption=ensure_text(message.caption),
                duration_seconds=message.voice.duration,
                file_size=message.voice.file_size,
            )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while queueing a voice message")
            await message.answer(AUDIO_HANDLER_ERROR)
            return

        await message.answer(BACKGROUND_JOB_ACCEPTED_TEXT.format(job_id=job.job_id))

    @router.message(F.audio)
    async def audio_handler(message: Message) -> None:
        if not is_allowed(message) or message.audio is None or message.from_user is None:
            return

        try:
            job = await deps.background_job_service.enqueue_audio(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                file_id=message.audio.file_id,
                file_unique_id=message.audio.file_unique_id,
                file_name=message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3",
                caption=ensure_text(message.caption),
                duration_seconds=message.audio.duration,
                file_size=message.audio.file_size,
            )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while queueing an audio file")
            await message.answer(AUDIO_HANDLER_ERROR)
            return

        await message.answer(BACKGROUND_JOB_ACCEPTED_TEXT.format(job_id=job.job_id))

    @router.message(F.photo)
    async def photo_handler(message: Message) -> None:
        if not is_allowed(message) or not message.photo or message.from_user is None:
            return

        photo = message.photo[-1]
        try:
            job = await deps.background_job_service.enqueue_photo(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                file_id=photo.file_id,
                file_unique_id=photo.file_unique_id,
                caption=ensure_text(message.caption),
                file_size=photo.file_size,
            )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while queueing a photo")
            await message.answer(AUDIO_HANDLER_ERROR)
            return

        await message.answer(BACKGROUND_JOB_ACCEPTED_TEXT.format(job_id=job.job_id))

    @router.message(F.document)
    async def document_handler(message: Message) -> None:
        if not is_allowed(message) or message.document is None or message.from_user is None:
            return

        try:
            job = await deps.background_job_service.enqueue_document(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                file_id=message.document.file_id,
                file_name=message.document.file_name or "document",
                mime_type=message.document.mime_type,
                caption=ensure_text(message.caption),
                file_size=message.document.file_size,
            )
        except ContentExtractionError as exc:
            await message.answer(str(exc))
            return
        except Exception:
            logger.exception("Unexpected error while queueing a document")
            await message.answer(AUDIO_HANDLER_ERROR)
            return

        await message.answer(BACKGROUND_JOB_ACCEPTED_TEXT.format(job_id=job.job_id))

    @router.message(F.text)
    async def text_handler(message: Message) -> None:
        if not is_allowed(message) or message.from_user is None:
            return

        text = ensure_text(message.text)
        if not text:
            await message.answer(EMPTY_MESSAGE_TEXT)
            return

        status_message = await show_processing(message)
        try:
            result = await deps.chat_service.handle_text_message(
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
        finally:
            await finish_processing(status_message)

        await send_response(message, str(result["content"]))

    return router
