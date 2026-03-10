# tg-ai-assistant

<p align="center">
  Private Telegram AI assistant with OpenRouter, SQLite memory, files, images, and voice support.
</p>

<p align="center">
  <a href="#english">English</a> •
  <a href="#russian">Русский</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/telegram-bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/openrouter-AI-black?style=for-the-badge" alt="OpenRouter">
  <img src="https://img.shields.io/badge/sqlite-memory-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

<p align="center">
  GitHub repository: <a href="https://github.com/web3daemon/tg-ai-assistant">web3daemon/tg-ai-assistant</a>
</p>

<p align="center">
  <a href="https://github.com/web3daemon/tg-ai-assistant/stargazers">
    <img src="https://img.shields.io/github/stars/web3daemon/tg-ai-assistant?style=social" alt="GitHub stars">
  </a>
</p>

<p align="center">
  <img src="https://starchart.cc/web3daemon/tg-ai-assistant.svg" alt="Stargazers over time">
</p>

---

## English

### Overview

`tg-ai-assistant` is a private Telegram bot for personal use. It connects Telegram to AI models through OpenRouter and keeps persistent chat history in SQLite.

It is designed for local use first:
- no VPS required
- no webhook required
- polling mode
- strict single-user access control

### Features

- private Telegram bot with whitelist access by `user_id` and `chat_id`
- persistent SQLite chat memory
- OpenRouter integration with model selection via `.env`
- support for text, documents, images, voice messages, and audio files
- local speech-to-text with `faster-whisper`
- usage tracking for tokens and request cost
- chat export via `/export`
- graceful shutdown and file logging with rotation
- basic automated tests

### Supported Content

- text messages
- `.txt`
- `.pdf`
- `.docx`
- `.xlsx`
- Telegram photos
- image files
- voice messages
- audio files

### Commands

- `/start` — bot startup message
- `/help` — available features
- `/status` — current runtime settings
- `/usage` — usage and cost summary
- `/clear` — clear current chat history
- `/export` — export current chat history to a text file

### Project Structure

```text
src/
  bot/
  db/
  services/
  utils/
  config.py
  logging_setup.py
  main.py
tests/
requirements.txt
.env.example
```

### Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in your `.env` values:

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_ID`
- `ALLOWED_CHAT_ID`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`

Optional runtime tuning:

- `MAX_FILE_SIZE_MB`
- `MAX_EXTRACTED_TEXT_CHARS`
- `LONG_RESPONSE_AS_FILE_THRESHOLD`
- `WHISPER_MODEL_SIZE`
- `WHISPER_DEVICE`
- `WHISPER_COMPUTE_TYPE`
- `MAX_AUDIO_DURATION_SECONDS`

### Run

```powershell
python -m src.main
```

### Tests

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Notes

- The bot is optimized for private local usage.
- The first `faster-whisper` run may download the speech model.
- Some multimodal behavior depends on the selected OpenRouter model.

---

## Russian

### Описание

`tg-ai-assistant` — это личный Telegram-бот для приватного использования. Он связывает Telegram с AI-моделями через OpenRouter и хранит постоянную историю диалога в SQLite.

Проект изначально рассчитан на локальный запуск:
- без VPS
- без webhook
- в режиме polling
- с жестким доступом только для одного пользователя

### Возможности

- приватный Telegram-бот с whitelist-проверкой по `user_id` и `chat_id`
- постоянная память диалога в SQLite
- интеграция с OpenRouter и выбор модели через `.env`
- поддержка текста, документов, изображений, голосовых сообщений и аудиофайлов
- локальное распознавание речи через `faster-whisper`
- учет токенов и стоимости запросов
- экспорт истории через `/export`
- корректное завершение работы и логирование в файл с ротацией
- базовые автоматические тесты

### Поддерживаемый контент

- текстовые сообщения
- `.txt`
- `.pdf`
- `.docx`
- `.xlsx`
- фото из Telegram
- изображения как файлы
- голосовые сообщения
- аудиофайлы

### Команды

- `/start` — запуск бота
- `/help` — справка и возможности
- `/status` — текущие настройки
- `/usage` — статистика по токенам и стоимости
- `/clear` — очистка истории текущего чата
- `/export` — выгрузка истории текущего чата в текстовый файл

### Структура проекта

```text
src/
  bot/
  db/
  services/
  utils/
  config.py
  logging_setup.py
  main.py
tests/
requirements.txt
.env.example
```

### Установка

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Заполни `.env`:

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_ID`
- `ALLOWED_CHAT_ID`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`

Дополнительные лимиты и настройки:

- `MAX_FILE_SIZE_MB`
- `MAX_EXTRACTED_TEXT_CHARS`
- `LONG_RESPONSE_AS_FILE_THRESHOLD`
- `WHISPER_MODEL_SIZE`
- `WHISPER_DEVICE`
- `WHISPER_COMPUTE_TYPE`
- `MAX_AUDIO_DURATION_SECONDS`

### Запуск

```powershell
python -m src.main
```

### Тесты

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Примечания

- Бот оптимизирован под локальный личный сценарий.
- При первом запуске `faster-whisper` может скачать модель распознавания речи.
- Поведение мультимодальности зависит от выбранной модели в OpenRouter.
