import asyncio
import json
import logging
from dataclasses import dataclass

from aiogram import Bot

from src.bot.common import send_bot_response
from src.bot.messages import BACKGROUND_JOB_FAILED_TEXT, BACKGROUND_JOB_READY_TEXT
from src.config import settings
from src.db.models import BackgroundJobRecord, JobArtifactRecord
from src.db.repository import BackgroundJobRepository
from src.services.chat_service import ChatService
from src.services.content import ContentExtractionError, ensure_supported_file_size, extract_document, extract_image
from src.services.openrouter import OpenRouterError
from src.services.speech import SpeechToTextError, SpeechToTextService
from src.utils.telegram_files import download_telegram_file
from src.utils.text import ensure_text

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EnqueuedJob:
    job_id: int
    job_type: str


class BackgroundJobService:
    def __init__(
        self,
        repository: BackgroundJobRepository,
        chat_service: ChatService,
        speech_service: SpeechToTextService,
    ) -> None:
        self._repository = repository
        self._chat_service = chat_service
        self._speech_service = speech_service

    async def enqueue_voice(
        self,
        *,
        chat_id: int,
        user_id: int,
        file_id: str,
        file_unique_id: str,
        caption: str,
        duration_seconds: int,
        file_size: int | None,
    ) -> EnqueuedJob:
        ensure_supported_file_size(file_size)
        return await self._enqueue(
            chat_id=chat_id,
            user_id=user_id,
            job_type="voice",
            payload={
                "duration_seconds": duration_seconds,
            },
            artifact={
                "telegram_file_id": file_id,
                "telegram_file_unique_id": file_unique_id,
                "source_kind": "voice",
                "file_name": f"voice_{file_unique_id}.ogg",
                "file_size": file_size,
                "caption_text": caption,
            },
        )

    async def enqueue_audio(
        self,
        *,
        chat_id: int,
        user_id: int,
        file_id: str,
        file_unique_id: str,
        file_name: str,
        caption: str,
        duration_seconds: int,
        file_size: int | None,
    ) -> EnqueuedJob:
        ensure_supported_file_size(file_size)
        return await self._enqueue(
            chat_id=chat_id,
            user_id=user_id,
            job_type="audio",
            payload={
                "duration_seconds": duration_seconds,
            },
            artifact={
                "telegram_file_id": file_id,
                "telegram_file_unique_id": file_unique_id,
                "source_kind": "audio",
                "file_name": file_name,
                "file_size": file_size,
                "caption_text": caption,
            },
        )

    async def enqueue_photo(
        self,
        *,
        chat_id: int,
        user_id: int,
        file_id: str,
        file_unique_id: str,
        caption: str,
        file_size: int | None,
    ) -> EnqueuedJob:
        ensure_supported_file_size(file_size)
        return await self._enqueue(
            chat_id=chat_id,
            user_id=user_id,
            job_type="photo",
            payload={},
            artifact={
                "telegram_file_id": file_id,
                "telegram_file_unique_id": file_unique_id,
                "source_kind": "photo",
                "file_name": f"photo_{file_unique_id}.jpg",
                "file_size": file_size,
                "caption_text": caption,
            },
        )

    async def enqueue_document(
        self,
        *,
        chat_id: int,
        user_id: int,
        file_id: str,
        file_name: str,
        mime_type: str | None,
        caption: str,
        file_size: int | None,
    ) -> EnqueuedJob:
        ensure_supported_file_size(file_size)
        return await self._enqueue(
            chat_id=chat_id,
            user_id=user_id,
            job_type="document",
            payload={
                "mime_type": mime_type,
            },
            artifact={
                "telegram_file_id": file_id,
                "source_kind": "document",
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "caption_text": caption,
            },
        )

    async def run(self, bot: Bot) -> None:
        logger.info("Background job worker started")
        try:
            while True:
                processed = await self.process_next(bot)
                if processed:
                    continue
                await asyncio.sleep(settings.background_job_poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info("Background job worker stopped")
            raise

    async def process_next(self, bot: Bot) -> bool:
        job = await asyncio.to_thread(self._repository.claim_next_job)
        if job is None:
            return False

        try:
            answer = await self._process_job(bot, job)
        except (SpeechToTextError, ContentExtractionError, OpenRouterError) as exc:
            await asyncio.to_thread(self._repository.mark_failed, job.id, str(exc))
            await bot.send_message(job.chat_id, BACKGROUND_JOB_FAILED_TEXT.format(job_id=job.id, error=str(exc)))
            return True
        except Exception as exc:
            logger.exception("Unexpected error while processing background job %s", job.id)
            await asyncio.to_thread(self._repository.mark_failed, job.id, str(exc))
            await bot.send_message(job.chat_id, BACKGROUND_JOB_FAILED_TEXT.format(job_id=job.id, error="Внутренняя ошибка."))
            return True

        await asyncio.to_thread(self._repository.mark_completed, job.id)
        await bot.send_message(job.chat_id, BACKGROUND_JOB_READY_TEXT.format(job_id=job.id))
        await send_bot_response(bot, job.chat_id, answer)
        return True

    async def _enqueue(
        self,
        *,
        chat_id: int,
        user_id: int,
        job_type: str,
        payload: dict[str, object],
        artifact: dict[str, object],
    ) -> EnqueuedJob:
        job_id = await asyncio.to_thread(
            self._repository.create_job,
            chat_id=chat_id,
            user_id=user_id,
            job_type=job_type,
            payload=payload,
        )
        await asyncio.to_thread(self._repository.add_job_artifact, job_id=job_id, **artifact)
        return EnqueuedJob(job_id=job_id, job_type=job_type)

    async def _process_job(self, bot: Bot, job: BackgroundJobRecord) -> str:
        payload = json.loads(job.payload_json)
        artifacts = await asyncio.to_thread(self._repository.get_job_artifacts, job.id)
        artifact = artifacts[0] if artifacts else None

        if job.job_type == "voice":
            return await self._process_voice(bot, job, payload, artifact)
        if job.job_type == "audio":
            return await self._process_audio(bot, job, payload, artifact)
        if job.job_type == "photo":
            return await self._process_photo(bot, job, payload, artifact)
        if job.job_type == "document":
            return await self._process_document(bot, job, payload, artifact)

        raise RuntimeError(f"Unsupported background job type: {job.job_type}")

    async def _process_voice(
        self,
        bot: Bot,
        job: BackgroundJobRecord,
        payload: dict[str, object],
        artifact: JobArtifactRecord | None,
    ) -> str:
        if artifact is None:
            raise RuntimeError("Missing artifact for voice job")

        file_bytes, _mime_type = await download_telegram_file(bot, artifact.telegram_file_id)
        transcribed = await asyncio.to_thread(
            self._speech_service.transcribe,
            artifact.file_name or "voice.ogg",
            file_bytes,
            ensure_text(artifact.caption_text),
            int(payload["duration_seconds"]),
        )
        result = await self._chat_service.handle_user_request(
            chat_id=job.chat_id,
            user_id=job.user_id,
            user_log_content=transcribed.log_content,
            user_content=transcribed.model_text,
        )
        return str(result["content"])

    async def _process_audio(
        self,
        bot: Bot,
        job: BackgroundJobRecord,
        payload: dict[str, object],
        artifact: JobArtifactRecord | None,
    ) -> str:
        if artifact is None:
            raise RuntimeError("Missing artifact for audio job")

        file_bytes, _mime_type = await download_telegram_file(bot, artifact.telegram_file_id)
        transcribed = await asyncio.to_thread(
            self._speech_service.transcribe,
            artifact.file_name or "audio.mp3",
            file_bytes,
            ensure_text(artifact.caption_text),
            int(payload["duration_seconds"]),
        )
        result = await self._chat_service.handle_user_request(
            chat_id=job.chat_id,
            user_id=job.user_id,
            user_log_content=transcribed.log_content,
            user_content=transcribed.model_text,
        )
        return str(result["content"])

    async def _process_photo(
        self,
        bot: Bot,
        job: BackgroundJobRecord,
        payload: dict[str, object],
        artifact: JobArtifactRecord | None,
    ) -> str:
        if artifact is None:
            raise RuntimeError("Missing artifact for photo job")

        file_bytes, mime_type = await download_telegram_file(bot, artifact.telegram_file_id)
        extracted = await asyncio.to_thread(
            extract_image,
            artifact.file_name or "photo.jpg",
            artifact.mime_type or mime_type,
            file_bytes,
            ensure_text(artifact.caption_text),
        )
        result = await self._chat_service.handle_user_request(
            chat_id=job.chat_id,
            user_id=job.user_id,
            user_log_content=extracted.log_content,
            user_content=[
                {"type": "text", "text": extracted.prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{extracted.mime_type};base64,{extracted.base64_data}"},
                },
            ],
        )
        return str(result["content"])

    async def _process_document(
        self,
        bot: Bot,
        job: BackgroundJobRecord,
        payload: dict[str, object],
        artifact: JobArtifactRecord | None,
    ) -> str:
        if artifact is None:
            raise RuntimeError("Missing artifact for document job")

        file_bytes, detected_mime_type = await download_telegram_file(bot, artifact.telegram_file_id)
        mime_type = str(payload["mime_type"]) if payload.get("mime_type") is not None else (artifact.mime_type or detected_mime_type)

        if (mime_type or "").startswith("image/"):
            extracted_image = await asyncio.to_thread(
                extract_image,
                artifact.file_name or "image",
                mime_type,
                file_bytes,
                ensure_text(artifact.caption_text),
            )
            result = await self._chat_service.handle_user_request(
                chat_id=job.chat_id,
                user_id=job.user_id,
                user_log_content=extracted_image.log_content,
                user_content=[
                    {"type": "text", "text": extracted_image.prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{extracted_image.mime_type};base64,{extracted_image.base64_data}"},
                    },
                ],
            )
            return str(result["content"])

        extracted_document = await asyncio.to_thread(
            extract_document,
            artifact.file_name or "document",
            file_bytes,
            ensure_text(artifact.caption_text),
        )
        result = await self._chat_service.handle_user_request(
            chat_id=job.chat_id,
            user_id=job.user_id,
            user_log_content=extracted_document.log_content,
            user_content=extracted_document.model_text,
        )
        return str(result["content"])
