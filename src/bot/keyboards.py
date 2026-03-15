from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


MODE_CALLBACK_PREFIX = "mode:"
ACTION_CALLBACK_PREFIX = "action:"
AVAILABLE_MODES = ("chat", "summarize", "translate", "analyze")
MENU_BUTTON_TEXT = "Меню"
MODE_BUTTON_TEXT = "Режим"
STATUS_BUTTON_TEXT = "Статус"
SETTINGS_BUTTON_TEXT = "Настройки"


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Режимы", callback_data=f"{ACTION_CALLBACK_PREFIX}modes")
    builder.button(text="Статус", callback_data=f"{ACTION_CALLBACK_PREFIX}status")
    builder.button(text="Настройки", callback_data=f"{ACTION_CALLBACK_PREFIX}settings")
    builder.button(text="Очистить чат", callback_data=f"{ACTION_CALLBACK_PREFIX}clear")
    builder.adjust(2, 2)
    return builder.as_markup()


def build_modes_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for mode in AVAILABLE_MODES:
        prefix = "• " if mode == current_mode else ""
        builder.button(text=f"{prefix}{build_mode_label(mode)}", callback_data=f"{MODE_CALLBACK_PREFIX}{mode}")
    builder.button(text="Назад", callback_data=f"{ACTION_CALLBACK_PREFIX}menu")
    builder.adjust(2, 2)
    return builder.as_markup()


def build_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data=f"{ACTION_CALLBACK_PREFIX}menu")
    return builder.as_markup()


def build_persistent_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_BUTTON_TEXT), KeyboardButton(text=MODE_BUTTON_TEXT)],
            [KeyboardButton(text=STATUS_BUTTON_TEXT), KeyboardButton(text=SETTINGS_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Напиши сообщение или выбери действие",
    )


def build_mode_label(mode: str) -> str:
    labels = {
        "chat": "Чат",
        "summarize": "Саммари",
        "translate": "Перевод",
        "analyze": "Анализ",
    }
    return labels.get(mode, mode)
