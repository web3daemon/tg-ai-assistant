from dataclasses import dataclass

from aiogram.types import BufferedInputFile

from src.config import settings
from src.utils.formatting import render_telegram_html, strip_markup
from src.utils.text import split_text


@dataclass(slots=True)
class FormattedTextChunk:
    html_text: str
    plain_text: str


def build_response_payloads(text: str) -> list[FormattedTextChunk] | BufferedInputFile:
    if len(text) < settings.long_response_as_file_threshold:
        chunks = split_text(text, settings.telegram_message_chunk_size)
        return [
            FormattedTextChunk(
                html_text=render_telegram_html(chunk),
                plain_text=strip_markup(chunk),
            )
            for chunk in chunks
        ]

    return BufferedInputFile(text.encode("utf-8"), filename="response.txt")
