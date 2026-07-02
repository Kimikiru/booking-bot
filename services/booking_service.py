"""Бизнес-логика записи: рабочее время, свободные слоты, создание брони.

Время в проекте — наивное локальное (в часовом поясе бизнеса из config.tz).
Один мастер: слот занят, если пересекается с любой активной бронью на этот день.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from db.models import Booking, Service
from db.repositories.booking import BookingRepository
from db.repositories.service import ServiceRepository
from config import Settings


class SlotTakenError(Exception):
    """Выбранный слот уже занят (гонка двух клиентов)."""


class SlotInPastError(Exception):
    """Выбранный слот уже в прошлом."""


@dataclass(frozen=True)
class BusyInterval:
    start: datetime
    end: datetime


class BookingService:
    def __init__(self, session, settings: Settings) -> None:
        self.settings = settings
        self.services = ServiceRepository(session)
        self.bookings = BookingRepository(session)

    def now(self) -> datetime:
        """Текущее локальное время бизнеса (наивное)."""
        return datetime.now(self.settings.tzinfo).replace(tzinfo=None)

    def available_dates(self) -> list[date]:
        today = self.now().date()
        return [today + timedelta(days=i) for i in range(self.settings.booking_horizon_days)]

    async def _busy_intervals(self, day: date) -> list[BusyInterval]:
        day_start = datetime.combine(day, time.min)
        day_end = day_start + timedelta(days=1)
        bookings = await self.bookings.active_between(day_start, day_end)
        return [
            BusyInterval(
                start=b.start_at,
                end=b.start_at + timedelta(minutes=b.service.duration_min),
            )
            for b in bookings
        ]

    @staticmethod
    def _overlaps(start: datetime, end: datetime, busy: list[BusyInterval]) -> bool:
        return any(start < iv.end and iv.start < end for iv in busy)

    async def free_slots(self, service: Service, day: date) -> list[datetime]:
        """Свободные слоты для услуги на дату (с учётом занятости и прошлого)."""
        busy = await self._busy_intervals(day)
        now = self.now()
        duration = timedelta(minutes=service.duration_min)

        cursor = datetime.combine(day, time(hour=self.settings.work_start_hour))
        day_end = datetime.combine(day, time(hour=self.settings.work_end_hour))

        slots: list[datetime] = []
        while cursor + duration <= day_end:
            slot_end = cursor + duration
            if cursor > now and not self._overlaps(cursor, slot_end, busy):
                slots.append(cursor)
            cursor += duration
        return slots

    async def create_booking(
        self,
        *,
        service: Service,
        start_at: datetime,
        user_id: int,
        username: str | None,
        full_name: str | None,
        phone: str | None,
    ) -> Booking:
        """Создаёт бронь с повторной проверкой занятости (защита от гонки)."""
        if start_at <= self.now():
            raise SlotInPastError

        duration = timedelta(minutes=service.duration_min)
        busy = await self._busy_intervals(start_at.date())
        if self._overlaps(start_at, start_at + duration, busy):
            raise SlotTakenError

        return await self.bookings.create(
            user_id=user_id,
            username=username,
            full_name=full_name,
            phone=phone,
            service_id=service.id,
            start_at=start_at,
        )
