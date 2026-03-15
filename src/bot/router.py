from aiogram import Router

from src.bot.dependencies import BotDependencies
from src.bot.routers.commands import build_commands_router
from src.bot.routers.content import build_content_router
from src.services.chat_service import ChatService
from src.services.background_jobs import BackgroundJobService
from src.services.speech import SpeechToTextService


def build_router(
    chat_service: ChatService,
    speech_service: SpeechToTextService,
    background_job_service: BackgroundJobService,
) -> Router:
    deps = BotDependencies(
        chat_service=chat_service,
        speech_service=speech_service,
        background_job_service=background_job_service,
    )
    router = Router(name="root")
    router.include_router(build_commands_router(deps))
    router.include_router(build_content_router(deps))
    return router
