"""Клавиатуры сценария записи: услуги, даты, слоты, подтверждение."""
from __future__ import annotations

from datetime import date, datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Service
from keyboards.callbacks import DateCB, NavCB, ServiceCB, SlotCB

SLOT_FMT = "%Y%m%dT%H%M"

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def services_kb(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        price = f" — {svc.price}₽" if svc.price is not None else ""
        builder.button(
            text=f"{svc.title} ({svc.duration_min} мин){price}",
            callback_data=ServiceCB(service_id=svc.id),
        )
    builder.button(text="⬅️ В меню", callback_data=NavCB(to="menu"))
    builder.adjust(1)
    return builder.as_markup()


def dates_kb(days: list[date]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in days:
        label = f"{WEEKDAYS_RU[d.weekday()]} {d.strftime('%d.%m')}"
        builder.button(text=label, callback_data=DateCB(value=d.isoformat()))
    builder.button(text="⬅️ Назад к услугам", callback_data=NavCB(to="book_service"))
    builder.adjust(3)
    return builder.as_markup()


def slots_kb(slots: list[datetime]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.button(
            text=slot.strftime("%H:%M"),
            callback_data=SlotCB(value=slot.strftime(SLOT_FMT)),
        )
    builder.adjust(4)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к датам", callback_data=NavCB(to="book_date").pack()
        )
    )
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить заявку", callback_data="booking:submit")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data=NavCB(to="menu").pack())],
        ]
    )
