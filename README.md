<p align="center">
  <strong>Gemini Telegram Copilot</strong><br>
  Private Telegram AI assistant with OpenRouter, rolling memory, background jobs, modes, files, images, and voice support.
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

## English

### Overview

`Gemini Telegram Copilot` is a private Telegram bot for personal or small allowlist usage. It connects Telegram to AI models through OpenRouter, stores chat history in SQLite, summarizes older context into rolling memory, and handles heavy multimodal tasks in the background.

### Highlights

- allowlist-based access control for one or more Telegram users and chats
- text, documents, images, voice messages, and audio file support
- background queue for heavy media processing
- rolling memory: summary + recent messages
- chat modes: `chat`, `summarize`, `translate`, `analyze`
- mode-aware model routing with fallback models
- usage tracking for tokens and estimated cost
- chat export via `/export`
- inline menu and mode switching
- rotating logs and automated tests

### Commands

- `/start` - onboarding message with quick actions
- `/help` - feature overview
- `/menu` - inline quick actions
- `/mode` - switch mode
- `/status` - runtime limits and active model
- `/settings` - detailed runtime configuration
- `/usage` - token and cost summary
- `/clear` - clear current chat history
- `/export` - export current chat history

### Modes

- `chat` - default assistant mode
- `summarize` - compact summaries and action items
- `translate` - translation-focused answers
- `analyze` - structured analysis and recommendations

### Installation

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Run

```powershell
python -m src.main
```

### Tests

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Important `.env`

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_ID`
- `ALLOWED_CHAT_ID`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_FALLBACK_MODEL`
- `OPENROUTER_VISION_MODEL`
- `OPENROUTER_SUMMARY_MODEL`
- `OPENROUTER_TRANSLATE_MODEL`
- `OPENROUTER_ANALYZE_MODEL`
- `RECENT_MESSAGES_LIMIT`
- `SUMMARY_UPDATE_MIN_MESSAGES`
- `BACKGROUND_JOB_POLL_INTERVAL_SECONDS`

### Notes

- The bot is optimized for local polling-first usage.
- `faster-whisper` may download model files on first run.
- Vision behavior depends on the configured OpenRouter model set.
- Background jobs use SQLite-backed queueing inside the same process.

## Russian

### Описание

`Gemini Telegram Copilot` — это приватный Telegram-бот для личного использования или небольшого allowlist-сценария. Он подключает Telegram к AI-моделям через OpenRouter, хранит историю чатов в SQLite, сворачивает старый контекст в rolling summary memory и обрабатывает тяжелые мультимодальные задачи в фоне.

### Ключевые возможности

- allowlist-доступ для одного или нескольких пользователей и чатов
- поддержка текста, документов, изображений, голосовых сообщений и аудиофайлов
- фоновая очередь для тяжелой media-обработки
- память в формате `summary + recent messages`
- режимы работы: `chat`, `summarize`, `translate`, `analyze`
- mode-aware routing по моделям с fallback
- учет токенов и стоимости запросов
- экспорт чата через `/export`
- inline-меню и переключение режимов
- ротация логов и автотесты

### Команды

- `/start` - старт и быстрые действия
- `/help` - обзор возможностей
- `/menu` - inline-меню
- `/mode` - переключение режима
- `/status` - лимиты и активная модель
- `/settings` - подробные runtime-настройки
- `/usage` - статистика по токенам и стоимости
- `/clear` - очистка истории текущего чата
- `/export` - экспорт истории чата

### Режимы

- `chat` - обычный режим ассистента
- `summarize` - краткие саммари и action items
- `translate` - режим перевода
- `analyze` - структурный анализ и рекомендации

### Установка

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Запуск

```powershell
python -m src.main
```

### Тесты

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Важные `.env`

- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_ID`
- `ALLOWED_CHAT_ID`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_FALLBACK_MODEL`
- `OPENROUTER_VISION_MODEL`
- `OPENROUTER_SUMMARY_MODEL`
- `OPENROUTER_TRANSLATE_MODEL`
- `OPENROUTER_ANALYZE_MODEL`
- `RECENT_MESSAGES_LIMIT`
- `SUMMARY_UPDATE_MIN_MESSAGES`
- `BACKGROUND_JOB_POLL_INTERVAL_SECONDS`

### Примечания

- Бот оптимизирован под локальный polling-first сценарий.
- При первом запуске `faster-whisper` может скачать модель.
- Поведение vision зависит от выбранного набора моделей OpenRouter.
- Фоновые задачи работают через SQLite-backed очередь внутри того же процесса.
