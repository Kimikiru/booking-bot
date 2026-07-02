"""Общие клавиатуры: главное меню, кнопки отмены/контакта."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from keyboards.callbacks import NavCB

CANCEL_HINT = "Чтобы прервать — /cancel"


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записаться", callback_data=NavCB(to="book").pack())],
            [InlineKeyboardButton(text="🖼 Портфолио", callback_data=NavCB(to="portfolio").pack())],
        ]
    )


def to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В меню", callback_data=NavCB(to="menu").pack())]
        ]
    )


def contact_request_kb() -> ReplyKeyboardMarkup:
    """Reply-клавиатура: поделиться контактом одной кнопкой."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Или введите номер телефона вручную",
    )
