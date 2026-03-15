START_TEXT = (
    "Бот запущен. Отправь текст, документ, изображение или голосовое сообщение, "
    "и я передам это в модель через OpenRouter."
)

HELP_TEXT = (
    "Доступные команды:\n"
    "/start - запуск\n"
    "/help - помощь\n"
    "/menu - показать меню\n"
    "/mode - выбрать режим\n"
    "/settings - показать ключевые параметры\n"
    "/clear - очистить историю чата\n"
    "/status - показать текущие настройки\n"
    "/usage - показать расход по токенам и стоимости\n"
    "/export - выгрузить историю чата в файл\n\n"
    "Поддерживаются текст, документы .txt/.pdf/.docx/.xlsx, изображения, голосовые сообщения и аудиофайлы."
)

NO_USAGE_TEXT = "Пока нет данных по расходу. Сначала отправь хотя бы один запрос в модель."
EMPTY_MESSAGE_TEXT = "Пустое сообщение не обрабатывается."
CLEAR_RESULT_TEMPLATE = "История очищена. Удалено записей: {deleted}."

TEXT_HANDLER_ERROR = "Произошла внутренняя ошибка. Подробности записаны в лог."
VOICE_HANDLER_ERROR = "Не удалось обработать голосовое сообщение. Подробности записаны в лог."
AUDIO_HANDLER_ERROR = "Не удалось обработать аудиофайл. Подробности записаны в лог."
IMAGE_HANDLER_ERROR = "Не удалось обработать изображение. Подробности записаны в лог."
FILE_HANDLER_ERROR = "Не удалось обработать файл. Подробности записаны в лог."

LONG_RESPONSE_CAPTION = "Ответ слишком длинный, отправляю файлом."
EMPTY_EXPORT_TEXT = "История пуста. Экспортировать нечего."
EXPORT_CAPTION = "Экспорт истории чата."
PROCESSING_TEXT = "Обрабатываю запрос. Это может занять несколько секунд."
BACKGROUND_JOB_ACCEPTED_TEXT = "Задача #{job_id} поставлена в очередь. Отправлю результат отдельным сообщением."
BACKGROUND_JOB_READY_TEXT = "Задача #{job_id} завершена."
BACKGROUND_JOB_FAILED_TEXT = "Задача #{job_id} завершилась с ошибкой: {error}"
MODE_CHANGED_TEXT = "Режим переключен: {mode_label}."
MODE_PROMPT_TEXT = "Выбери режим работы."
MENU_TEXT = "Быстрые действия:"


def build_status_text(
    model: str,
    context_limit: int,
    recent_messages_limit: int,
    summary_update_min_messages: int,
    max_tokens: int,
    temperature: float,
    max_file_size_mb: int,
    max_extracted_text_chars: int,
    whisper_model_size: str,
    max_audio_duration_seconds: int,
) -> str:
    return (
        "Текущий статус:\n"
        f"model: {model}\n"
        f"context limit: {context_limit}\n"
        f"recent messages limit: {recent_messages_limit}\n"
        f"summary update min messages: {summary_update_min_messages}\n"
        f"max tokens: {max_tokens}\n"
        f"temperature: {temperature}\n"
        f"max file size: {max_file_size_mb} MB\n"
        f"max extracted text chars: {max_extracted_text_chars}\n"
        f"whisper model: {whisper_model_size}\n"
        f"max audio duration: {max_audio_duration_seconds}s\n"
        "user access: ok\n"
        "chat access: ok"
    )


def build_usage_text(last_usage: dict[str, float | int], summary: dict[str, float | int]) -> str:
    return (
        "Расход по чату:\n"
        f"last cost: ${last_usage['cost']:.6f}\n"
        f"last prompt tokens: {last_usage['prompt_tokens']}\n"
        f"last completion tokens: {last_usage['completion_tokens']}\n"
        f"last total tokens: {last_usage['total_tokens']}\n\n"
        f"requests total: {summary['requests']}\n"
        f"cost total: ${summary['cost']:.6f}\n"
        f"prompt tokens total: {summary['prompt_tokens']}\n"
        f"completion tokens total: {summary['completion_tokens']}\n"
        f"tokens total: {summary['total_tokens']}"
    )


def build_settings_text(
    model: str,
    fallback_model: str,
    vision_model: str,
    summary_model: str,
    translate_model: str,
    analyze_model: str,
    openrouter_base_url: str,
    request_timeout_seconds: float,
    max_retries: int,
    context_limit: int,
    recent_messages_limit: int,
    summary_update_min_messages: int,
    summary_max_chars: int,
    max_tokens: int,
    temperature: float,
    max_file_size_mb: int,
    max_extracted_text_chars: int,
    whisper_model_size: str,
    whisper_device: str,
    whisper_compute_type: str,
    max_audio_duration_seconds: int,
    allowed_users_count: int,
    allowed_chats_count: int,
) -> str:
    return (
        "Ключевые настройки:\n"
        f"model: {model}\n"
        f"fallback model: {fallback_model or '-'}\n"
        f"vision model: {vision_model or '-'}\n"
        f"summary model: {summary_model or '-'}\n"
        f"translate model: {translate_model or '-'}\n"
        f"analyze model: {analyze_model or '-'}\n"
        f"openrouter base url: {openrouter_base_url}\n"
        f"request timeout: {request_timeout_seconds}s\n"
        f"max retries: {max_retries}\n"
        f"context limit: {context_limit}\n"
        f"recent messages limit: {recent_messages_limit}\n"
        f"summary update min messages: {summary_update_min_messages}\n"
        f"summary max chars: {summary_max_chars}\n"
        f"max tokens: {max_tokens}\n"
        f"temperature: {temperature}\n"
        f"max file size: {max_file_size_mb} MB\n"
        f"max extracted text chars: {max_extracted_text_chars}\n"
        f"whisper model: {whisper_model_size}\n"
        f"whisper device: {whisper_device}\n"
        f"whisper compute type: {whisper_compute_type}\n"
        f"max audio duration: {max_audio_duration_seconds}s\n"
        f"allowed users: {allowed_users_count}\n"
        f"allowed chats: {allowed_chats_count}"
    )


def build_start_text(current_mode: str, mode_label: str) -> str:
    return (
        "Бот запущен.\n"
        f"Текущий режим: {mode_label}.\n"
        "Можно отправлять текст, документы, изображения, голосовые сообщения и аудиофайлы."
    )
