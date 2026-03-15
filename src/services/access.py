from aiogram.types import CallbackQuery, Message

from src.config import settings


def is_allowed_message(message: Message) -> bool:
    from_user = message.from_user
    if from_user is None:
        return False

    if from_user.id not in settings.allowed_telegram_user_ids_set:
        return False

    if message.chat.id not in settings.allowed_chat_ids_set:
        return False

    return message.chat.type == "private"


def is_allowed_callback(callback: CallbackQuery) -> bool:
    if callback.message is None or callback.from_user is None:
        return False

    if callback.from_user.id not in settings.allowed_telegram_user_ids_set:
        return False

    return (
        callback.message.chat.id in settings.allowed_chat_ids_set
        and callback.message.chat.type == "private"
    )
