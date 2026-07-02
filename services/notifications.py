"""Уведомления админу о новых заявках."""
from __future__ import annotations

import logging

from aiogram import Bot

from db.models import Booking
from keyboards.admin import admin_actions_kb

logger = logging.getLogger(__name__)


def format_new_booking(booking: Booking) -> str:
    when = booking.start_at.strftime("%d.%m.%Y %H:%M")
    username = f"@{booking.username}" if booking.username else "—"
    return (
        "🆕 <b>Новая заявка</b>\n\n"
        f"Услуга: <b>{booking.service.title}</b>\n"
        f"Когда: <b>{when}</b>\n"
        f"Имя: {booking.full_name or '—'}\n"
        f"Телефон: {booking.phone or '—'}\n"
        f"Telegram: {username} (id {booking.user_id})\n"
        f"Заявка №{booking.id}"
    )


async def notify_admin_new_booking(bot: Bot, admin_id: int, booking: Booking) -> None:
    """Шлём заявку админу. Ошибка доставки не должна ронять сценарий клиента."""
    try:
        await bot.send_message(
            admin_id,
            format_new_booking(booking),
            reply_markup=admin_actions_kb(booking.id),
        )
    except Exception:
        logger.exception("Не удалось уведомить админа о заявке %s", booking.id)
