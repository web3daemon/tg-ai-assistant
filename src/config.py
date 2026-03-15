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
    allowed_telegram_user_ids: str = Field(alias="ALLOWED_TELEGRAM_USER_IDS", default="")
    allowed_chat_ids: str = Field(alias="ALLOWED_CHAT_IDS", default="")

    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(alias="OPENROUTER_MODEL")
    openrouter_fallback_model: str = Field(alias="OPENROUTER_FALLBACK_MODEL", default="")
    openrouter_vision_model: str = Field(alias="OPENROUTER_VISION_MODEL", default="")
    openrouter_summary_model: str = Field(alias="OPENROUTER_SUMMARY_MODEL", default="")
    openrouter_translate_model: str = Field(alias="OPENROUTER_TRANSLATE_MODEL", default="")
    openrouter_analyze_model: str = Field(alias="OPENROUTER_ANALYZE_MODEL", default="")
    openrouter_base_url: str = Field(alias="OPENROUTER_BASE_URL")
    openrouter_timeout_seconds: float = Field(alias="OPENROUTER_TIMEOUT_SECONDS", default=120.0)
    openrouter_max_retries: int = Field(alias="OPENROUTER_MAX_RETRIES", default=2)
    openrouter_retry_backoff_seconds: float = Field(alias="OPENROUTER_RETRY_BACKOFF_SECONDS", default=1.5)

    model_temperature: float = Field(alias="MODEL_TEMPERATURE", default=0.4)
    model_max_tokens: int = Field(alias="MODEL_MAX_TOKENS", default=2000)
    context_messages_limit: int = Field(alias="CONTEXT_MESSAGES_LIMIT", default=12)
    recent_messages_limit: int = Field(alias="RECENT_MESSAGES_LIMIT", default=6)
    summary_update_min_messages: int = Field(alias="SUMMARY_UPDATE_MIN_MESSAGES", default=8)
    summary_max_chars: int = Field(alias="SUMMARY_MAX_CHARS", default=4000)
    summary_source_max_chars: int = Field(alias="SUMMARY_SOURCE_MAX_CHARS", default=12000)
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
    background_job_poll_interval_seconds: float = Field(alias="BACKGROUND_JOB_POLL_INTERVAL_SECONDS", default=1.0)

    @property
    def allowed_telegram_user_ids_set(self) -> set[int]:
        return self._parse_allowlist(self.allowed_telegram_user_ids, self.allowed_telegram_user_id)

    @property
    def allowed_chat_ids_set(self) -> set[int]:
        return self._parse_allowlist(self.allowed_chat_ids, self.allowed_chat_id)

    @staticmethod
    def _parse_allowlist(raw_value: str, fallback_value: int) -> set[int]:
        values = {
            int(item.strip())
            for item in raw_value.split(",")
            if item.strip()
        }
        values.add(fallback_value)
        return values


settings = Settings()
