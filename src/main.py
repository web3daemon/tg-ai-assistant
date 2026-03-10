import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.bot.handlers import build_router
from src.config import settings
from src.db.repository import ChatRepository
from src.db.session import init_db
from src.logging_setup import configure_logging
from src.services.chat_service import ChatService
from src.services.openrouter import OpenRouterClient
from src.services.speech import SpeechToTextService


async def main() -> None:
    configure_logging()
    init_db()

    logger = logging.getLogger(__name__)
    logger.info("Starting bot")

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dispatcher = Dispatcher()

    repository = ChatRepository()
    ai_client = OpenRouterClient()
    speech_service = SpeechToTextService()
    chat_service = ChatService(repository=repository, ai_client=ai_client)

    dispatcher.include_router(build_router(chat_service, speech_service))

    try:
        await dispatcher.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    finally:
        await bot.session.close()
        logger.info("Bot session closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot stopped by user")
