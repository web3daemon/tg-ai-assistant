from dataclasses import dataclass

from src.services.chat_service import ChatService
from src.services.background_jobs import BackgroundJobService
from src.services.speech import SpeechToTextService


@dataclass(slots=True)
class BotDependencies:
    chat_service: ChatService
    speech_service: SpeechToTextService
    background_job_service: BackgroundJobService
