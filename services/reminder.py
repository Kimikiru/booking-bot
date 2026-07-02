"""Фоновые напоминания на APScheduler.

Раз в минуту сканируем подтверждённые брони, до начала которых осталось
не больше reminder_before_hours, и шлём клиенту напоминание. Скан-подход
переживает рестарт бота (в отличие от джоб-стора в памяти).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config import Settings
from db.models import Booking
from db.repositories.booking import BookingRepository

logger = logging.getLogger(__name__)


def _reminder_text(booking: Booking) -> str:
    when = booking.start_at.strftime("%d.%m в %H:%M")
    return (
        "🔔 <b>Напоминание о записи</b>\n\n"
        f"Услуга: <b>{booking.service.title}</b>\n"
        f"Когда: <b>{when}</b>\n\n"
        "Ждём вас! Если планы изменились — напишите нам."
    )


async def _run_reminder_tick(
    bot: Bot,
    session_pool: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    now = datetime.now(settings.tzinfo).replace(tzinfo=None)
    until = now + timedelta(hours=settings.reminder_before_hours)

    async with session_pool() as session:
        repo = BookingRepository(session)
        due = await repo.due_for_reminder(now, until)
        for booking in due:
            try:
                await bot.send_message(booking.user_id, _reminder_text(booking))
                await repo.mark_reminded(booking)
                logger.info("Напоминание отправлено: booking=%s", booking.id)
            except TelegramForbiddenError:
                # Клиент заблокировал бота — достучаться нельзя, помечаем, чтобы не долбить.
                await repo.mark_reminded(booking)
                logger.warning("Клиент %s заблокировал бота", booking.user_id)
            except Exception:
                logger.exception("Не удалось отправить напоминание booking=%s", booking.id)
        await session.commit()


def setup_scheduler(
    bot: Bot,
    session_pool: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(
        _run_reminder_tick,
        trigger="interval",
        minutes=1,
        args=(bot, session_pool, settings),
        id="reminder_tick",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
