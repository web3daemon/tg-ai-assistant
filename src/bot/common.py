import logging
from collections.abc import Sequence

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from src.bot.keyboards import build_persistent_reply_keyboard
from src.bot.messages import LONG_RESPONSE_CAPTION
from src.services.access import is_allowed_callback, is_allowed_message
from src.services.content import ExtractedImage
from src.utils.responses import FormattedTextChunk, build_response_payloads

logger = logging.getLogger(__name__)


def is_allowed(message: Message) -> bool:
    return is_allowed_message(message)


def is_allowed_query(callback: CallbackQuery) -> bool:
    return is_allowed_callback(callback)


async def show_processing(message: Message) -> Message | None:
    await message.bot.send_chat_action(message.chat.id, "typing")
    return None


async def finish_processing(status_message: Message | None) -> None:
    if status_message is None:
        return

    try:
        await status_message.delete()
    except TelegramBadRequest:
        logger.debug("Processing message could not be deleted", exc_info=True)


def image_prompt_payload(extracted: ExtractedImage) -> list[dict[str, object]]:
    return [
        {"type": "text", "text": extracted.prompt_text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{extracted.mime_type};base64,{extracted.base64_data}"
            },
        },
    ]


async def send_response(message: Message, answer: str) -> None:
    payload = build_response_payloads(answer)
    if isinstance(payload, BufferedInputFile):
        await message.answer_document(
            payload,
            caption=LONG_RESPONSE_CAPTION,
            reply_markup=build_persistent_reply_keyboard(),
        )
        return

    await send_text_chunks(message, payload)


async def send_bot_response(bot: Bot, chat_id: int, answer: str) -> None:
    payload = build_response_payloads(answer)
    if isinstance(payload, BufferedInputFile):
        await bot.send_document(
            chat_id,
            payload,
            caption=LONG_RESPONSE_CAPTION,
            reply_markup=build_persistent_reply_keyboard(),
        )
        return

    for index, chunk in enumerate(payload):
        try:
            await bot.send_message(
                chat_id,
                chunk.html_text,
                parse_mode="HTML",
                reply_markup=build_persistent_reply_keyboard() if index == 0 else None,
            )
        except TelegramBadRequest:
            await bot.send_message(
                chat_id,
                chunk.plain_text,
                parse_mode=None,
                reply_markup=build_persistent_reply_keyboard() if index == 0 else None,
            )


async def send_text_chunks(message: Message, chunks: Sequence[FormattedTextChunk]) -> None:
    for index, chunk in enumerate(chunks):
        try:
            await message.answer(
                chunk.html_text,
                parse_mode="HTML",
                reply_markup=build_persistent_reply_keyboard() if index == 0 else None,
            )
        except TelegramBadRequest:
            await message.answer(
                chunk.plain_text,
                parse_mode=None,
                reply_markup=build_persistent_reply_keyboard() if index == 0 else None,
            )
