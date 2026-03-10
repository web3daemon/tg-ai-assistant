from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    allowed_telegram_user_id: int = Field(alias="ALLOWED_TELEGRAM_USER_ID")
    allowed_chat_id: int = Field(alias="ALLOWED_CHAT_ID")

    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(alias="OPENROUTER_BASE_URL")

    model_temperature: float = Field(alias="MODEL_TEMPERATURE", default=0.4)
    model_max_tokens: int = Field(alias="MODEL_MAX_TOKENS", default=2000)
    context_messages_limit: int = Field(alias="CONTEXT_MESSAGES_LIMIT", default=12)
    system_prompt: str = Field(alias="SYSTEM_PROMPT")

    sqlite_path: Path = Field(alias="SQLITE_PATH", default=Path("data/bot.db"))
    log_file_path: Path = Field(alias="LOG_FILE_PATH", default=Path("logs/bot.log"))
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")
    log_max_bytes: int = Field(alias="LOG_MAX_BYTES", default=1_048_576)
    log_backup_count: int = Field(alias="LOG_BACKUP_COUNT", default=5)
    telegram_message_chunk_size: int = Field(alias="TELEGRAM_MESSAGE_CHUNK_SIZE", default=4000)
    long_response_as_file_threshold: int = Field(alias="LONG_RESPONSE_AS_FILE_THRESHOLD", default=12000)
    max_file_size_mb: int = Field(alias="MAX_FILE_SIZE_MB", default=10)
    max_extracted_text_chars: int = Field(alias="MAX_EXTRACTED_TEXT_CHARS", default=30000)
    whisper_model_size: str = Field(alias="WHISPER_MODEL_SIZE", default="small")
    whisper_device: str = Field(alias="WHISPER_DEVICE", default="auto")
    whisper_compute_type: str = Field(alias="WHISPER_COMPUTE_TYPE", default="auto")
    max_audio_duration_seconds: int = Field(alias="MAX_AUDIO_DURATION_SECONDS", default=600)


settings = Settings()
