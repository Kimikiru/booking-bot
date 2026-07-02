"""Клавиатура галереи портфолио: листание ← → и счётчик."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.callbacks import NavCB, PortfolioCB


def gallery_kb(offset: int, total: int) -> InlineKeyboardMarkup:
    nav_row: list[InlineKeyboardButton] = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=PortfolioCB(offset=offset - 1).pack()
            )
        )
    nav_row.append(
        InlineKeyboardButton(text=f"{offset + 1}/{total}", callback_data="noop")
    )
    if offset < total - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="➡️", callback_data=PortfolioCB(offset=offset + 1).pack()
            )
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav_row,
            [InlineKeyboardButton(text="📝 Записаться", callback_data=NavCB(to="book").pack())],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data=NavCB(to="menu").pack())],
        ]
    )
