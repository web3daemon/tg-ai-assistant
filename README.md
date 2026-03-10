# Telegram AI Bot

Локальный Telegram-бот для личного использования с доступом к AI-модели через OpenRouter.

## Возможности

- локальный запуск через `polling`
- доступ только для одного пользователя
- текстовый диалог с памятью в SQLite
- поддержка документов `.txt`, `.pdf`, `.docx`, `.xlsx`
- поддержка изображений как фото и как файла
- поддержка голосовых сообщений и аудиофайлов через локальный `faster-whisper`
- экспорт истории чата через `/export`
- `system prompt`
- команды `/start`, `/help`, `/clear`, `/status`, `/usage`, `/export`
- логирование в консоль и файл с ротацией
- длинные ответы разбиваются на части или отправляются файлом

## Требования

- Python 3.12+
- Telegram Bot Token
- OpenRouter API key

## Установка

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Заполни `.env` своими значениями:

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_ID`
- `ALLOWED_CHAT_ID`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`

При необходимости настрой лимиты:

- `MAX_FILE_SIZE_MB`
- `MAX_EXTRACTED_TEXT_CHARS`
- `LONG_RESPONSE_AS_FILE_THRESHOLD`
- `WHISPER_MODEL_SIZE`
- `WHISPER_DEVICE`
- `WHISPER_COMPUTE_TYPE`
- `MAX_AUDIO_DURATION_SECONDS`

## Запуск

```powershell
python -m src.main
```

## Проверка

После запуска можно проверить:

- обычный текстовый запрос
- `/usage`
- `/export`
- загрузку `.txt` или `.pdf`
- фото
- короткое голосовое сообщение

## Автотесты

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```
