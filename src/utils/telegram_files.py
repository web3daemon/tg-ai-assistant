import io
import mimetypes

from aiogram import Bot


async def download_telegram_file(bot: Bot, file_id: str) -> tuple[bytes, str | None]:
    telegram_file = await bot.get_file(file_id)
    buffer = io.BytesIO()
    await bot.download(telegram_file, destination=buffer)
    return buffer.getvalue(), _guess_mime_type(telegram_file.file_path)


def _guess_mime_type(file_path: str | None) -> str | None:
    if not file_path:
        return None
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type
