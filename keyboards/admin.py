"""Клавиатура админа под заявкой: подтвердить / отклонить."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import AdminCB


def admin_actions_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=AdminCB(action="confirm", booking_id=booking_id).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=AdminCB(action="reject", booking_id=booking_id).pack(),
                ),
            ]
        ]
    )
