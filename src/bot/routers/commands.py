from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.common import is_allowed, is_allowed_query
from src.bot.dependencies import BotDependencies
from src.bot.keyboards import (
    ACTION_CALLBACK_PREFIX,
    AVAILABLE_MODES,
    MENU_BUTTON_TEXT,
    MODE_CALLBACK_PREFIX,
    MODE_BUTTON_TEXT,
    SETTINGS_BUTTON_TEXT,
    STATUS_BUTTON_TEXT,
    build_back_keyboard,
    build_main_menu_keyboard,
    build_mode_label,
    build_modes_keyboard,
    build_persistent_reply_keyboard,
)
from src.bot.messages import (
    CLEAR_RESULT_TEMPLATE,
    EMPTY_EXPORT_TEXT,
    EXPORT_CAPTION,
    HELP_TEXT,
    MENU_TEXT,
    MODE_CHANGED_TEXT,
    MODE_PROMPT_TEXT,
    NO_USAGE_TEXT,
    build_settings_text,
    build_start_text,
    build_status_text,
    build_usage_text,
)
from src.config import settings


def build_commands_router(deps: BotDependencies) -> Router:
    router = Router(name="commands")

    @router.message(Command("start"))
    async def start_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        current_mode = await deps.chat_service.get_chat_mode(message.chat.id)
        await message.answer(
            build_start_text(current_mode, build_mode_label(current_mode)),
            reply_markup=build_persistent_reply_keyboard(),
        )

    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        await message.answer(HELP_TEXT, reply_markup=build_persistent_reply_keyboard())

    @router.message(Command("menu"))
    async def menu_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        await message.answer(MENU_TEXT, reply_markup=build_main_menu_keyboard())

    @router.message(Command("mode"))
    async def mode_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        current_mode = await deps.chat_service.get_chat_mode(message.chat.id)
        await message.answer(MODE_PROMPT_TEXT, reply_markup=build_modes_keyboard(current_mode))

    @router.message(F.text == MENU_BUTTON_TEXT)
    async def menu_button_handler(message: Message) -> None:
        await menu_handler(message)

    @router.message(F.text == MODE_BUTTON_TEXT)
    async def mode_button_handler(message: Message) -> None:
        await mode_handler(message)

    @router.message(F.text == STATUS_BUTTON_TEXT)
    async def status_button_handler(message: Message) -> None:
        await status_handler(message)

    @router.message(F.text == SETTINGS_BUTTON_TEXT)
    async def settings_button_handler(message: Message) -> None:
        await settings_handler(message)

    @router.message(Command("status"))
    async def status_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        await message.answer(_build_status_payload(), reply_markup=build_persistent_reply_keyboard())

    @router.message(Command("settings"))
    async def settings_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        await message.answer(
            _build_settings_payload(),
            reply_markup=build_persistent_reply_keyboard(),
            disable_web_page_preview=True,
        )

    @router.message(Command("usage"))
    async def usage_handler(message: Message) -> None:
        if not is_allowed(message):
            return

        last_usage = await deps.chat_service.get_last_request_usage(message.chat.id)
        summary = await deps.chat_service.get_usage_summary(message.chat.id)

        if last_usage is None:
            await message.answer(NO_USAGE_TEXT)
            return

        await message.answer(build_usage_text(last_usage, summary), reply_markup=build_persistent_reply_keyboard())

    @router.message(Command("clear"))
    async def clear_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        deleted = await deps.chat_service.clear_chat(message.chat.id)
        await message.answer(CLEAR_RESULT_TEMPLATE.format(deleted=deleted), reply_markup=build_persistent_reply_keyboard())

    @router.message(Command("export"))
    async def export_handler(message: Message) -> None:
        if not is_allowed(message):
            return
        export_file = await deps.chat_service.export_chat(message.chat.id)
        if export_file is None:
            await message.answer(EMPTY_EXPORT_TEXT, reply_markup=build_persistent_reply_keyboard())
            return
        await message.answer_document(export_file, caption=EXPORT_CAPTION, reply_markup=build_persistent_reply_keyboard())

    @router.callback_query(F.data == f"{ACTION_CALLBACK_PREFIX}modes")
    async def show_modes_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return
        current_mode = await deps.chat_service.get_chat_mode(callback.message.chat.id)
        await callback.message.edit_text(MODE_PROMPT_TEXT, reply_markup=build_modes_keyboard(current_mode))
        await callback.answer()

    @router.callback_query(F.data == f"{ACTION_CALLBACK_PREFIX}menu")
    async def menu_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return
        current_mode = await deps.chat_service.get_chat_mode(callback.message.chat.id)
        await callback.message.edit_text(
            build_start_text(current_mode, build_mode_label(current_mode)),
            reply_markup=build_main_menu_keyboard(),
        )
        await callback.answer()

    @router.callback_query(F.data == f"{ACTION_CALLBACK_PREFIX}status")
    async def status_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return
        await callback.message.edit_text(_build_status_payload(), reply_markup=build_back_keyboard())
        await callback.answer()

    @router.callback_query(F.data == f"{ACTION_CALLBACK_PREFIX}settings")
    async def settings_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return
        await callback.message.edit_text(
            _build_settings_payload(),
            reply_markup=build_back_keyboard(),
            disable_web_page_preview=True,
        )
        await callback.answer()

    @router.callback_query(F.data == f"{ACTION_CALLBACK_PREFIX}clear")
    async def clear_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return
        deleted = await deps.chat_service.clear_chat(callback.message.chat.id)
        await callback.message.answer(CLEAR_RESULT_TEMPLATE.format(deleted=deleted))
        await callback.answer()

    @router.callback_query(F.data.startswith(MODE_CALLBACK_PREFIX))
    async def mode_callback(callback: CallbackQuery) -> None:
        if callback.message is None or not is_allowed_query(callback):
            await callback.answer()
            return

        mode = callback.data.removeprefix(MODE_CALLBACK_PREFIX) if callback.data else "chat"
        if mode not in AVAILABLE_MODES:
            await callback.answer("Неизвестный режим", show_alert=True)
            return

        await deps.chat_service.set_chat_mode(callback.message.chat.id, mode)
        await callback.message.edit_text(
            MODE_CHANGED_TEXT.format(mode_label=build_mode_label(mode)),
            reply_markup=build_modes_keyboard(mode),
        )
        await callback.answer()

    return router


def _build_status_payload() -> str:
    return build_status_text(
        model=settings.openrouter_model,
        context_limit=settings.context_messages_limit,
        recent_messages_limit=settings.recent_messages_limit,
        summary_update_min_messages=settings.summary_update_min_messages,
        max_tokens=settings.model_max_tokens,
        temperature=settings.model_temperature,
        max_file_size_mb=settings.max_file_size_mb,
        max_extracted_text_chars=settings.max_extracted_text_chars,
        whisper_model_size=settings.whisper_model_size,
        max_audio_duration_seconds=settings.max_audio_duration_seconds,
    )


def _build_settings_payload() -> str:
    return build_settings_text(
        model=settings.openrouter_model,
        fallback_model=settings.openrouter_fallback_model,
        vision_model=settings.openrouter_vision_model,
        summary_model=settings.openrouter_summary_model,
        translate_model=settings.openrouter_translate_model,
        analyze_model=settings.openrouter_analyze_model,
        openrouter_base_url=settings.openrouter_base_url,
        request_timeout_seconds=settings.openrouter_timeout_seconds,
        max_retries=settings.openrouter_max_retries,
        context_limit=settings.context_messages_limit,
        recent_messages_limit=settings.recent_messages_limit,
        summary_update_min_messages=settings.summary_update_min_messages,
        summary_max_chars=settings.summary_max_chars,
        max_tokens=settings.model_max_tokens,
        temperature=settings.model_temperature,
        max_file_size_mb=settings.max_file_size_mb,
        max_extracted_text_chars=settings.max_extracted_text_chars,
        whisper_model_size=settings.whisper_model_size,
        whisper_device=settings.whisper_device,
        whisper_compute_type=settings.whisper_compute_type,
        max_audio_duration_seconds=settings.max_audio_duration_seconds,
        allowed_users_count=len(settings.allowed_telegram_user_ids_set),
        allowed_chats_count=len(settings.allowed_chat_ids_set),
    )
