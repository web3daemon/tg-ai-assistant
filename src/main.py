import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.app_meta import APP_NAME, APP_VERSION
from src.bot.router import build_router
from src.config import settings
from src.db.repository import BackgroundJobRepository, ChatRepository, ChatSettingsRepository
from src.db.session import init_db
from src.logging_setup import configure_logging
from src.services.background_jobs import BackgroundJobService
from src.services.chat_service import ChatService
from src.services.openrouter import OpenRouterClient
from src.services.speech import SpeechToTextService


async def main() -> None:
    configure_logging()
    init_db()

    logger = logging.getLogger(__name__)
    logger.info("Starting bot | app=%s version=%s model=%s", APP_NAME, APP_VERSION, settings.openrouter_model)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dispatcher = Dispatcher()

    repository = ChatRepository()
    chat_settings_repository = ChatSettingsRepository()
    background_job_repository = BackgroundJobRepository()
    ai_client = OpenRouterClient()
    speech_service = SpeechToTextService()
    chat_service = ChatService(
        repository=repository,
        ai_client=ai_client,
        settings_repository=chat_settings_repository,
    )
    background_job_service = BackgroundJobService(
        repository=background_job_repository,
        chat_service=chat_service,
        speech_service=speech_service,
    )

    dispatcher.include_router(build_router(chat_service, speech_service, background_job_service))
    background_worker_task = asyncio.create_task(background_job_service.run(bot))

    try:
        await dispatcher.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    finally:
        background_worker_task.cancel()
        await asyncio.gather(background_worker_task, return_exceptions=True)
        await ai_client.close()
        await bot.session.close()
        logger.info("Bot session closed | app=%s version=%s", APP_NAME, APP_VERSION)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot stopped by user | app=%s version=%s", APP_NAME, APP_VERSION)
