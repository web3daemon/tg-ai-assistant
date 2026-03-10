START_TEXT = (
    "Бот запущен. Отправь текст, документ, изображение или голосовое, "
    "и я передам это в модель через OpenRouter."
)

HELP_TEXT = (
    "Доступные команды:\n"
    "/start - запуск\n"
    "/help - помощь\n"
    "/clear - очистить историю чата\n"
    "/status - показать текущие настройки\n"
    "/usage - показать расход по токенам и стоимости\n"
    "/export - выгрузить историю чата в файл\n\n"
    "Поддерживаются текст, документы .txt/.pdf/.docx/.xlsx, изображения и голосовые сообщения."
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


def build_status_text(
    model: str,
    context_limit: int,
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
