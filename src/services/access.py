from aiogram.types import Message

from src.config import settings


def is_allowed_message(message: Message) -> bool:
    from_user = message.from_user
    if from_user is None:
        return False

    if from_user.id != settings.allowed_telegram_user_id:
        return False

    if message.chat.id != settings.allowed_chat_id:
        return False

    return message.chat.type == "private"
