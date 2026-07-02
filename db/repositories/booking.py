"""Репозиторий броней — весь доступ к таблице bookings."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models import Booking, BookingStatus

# Статусы, которые занимают время в расписании.
ACTIVE_STATUSES = (BookingStatus.pending, BookingStatus.confirmed)


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, booking_id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(Booking.id == booking_id)
        )
        return result.scalars().first()

    async def active_between(self, start: datetime, end: datetime) -> list[Booking]:
        """Активные брони, начинающиеся в интервале [start, end)."""
        result = await self.session.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(
                Booking.status.in_(ACTIVE_STATUSES),
                Booking.start_at >= start,
                Booking.start_at < end,
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: int,
        username: str | None,
        full_name: str | None,
        phone: str | None,
        service_id: int,
        start_at: datetime,
    ) -> Booking:
        booking = Booking(
            user_id=user_id,
            username=username,
            full_name=full_name,
            phone=phone,
            service_id=service_id,
            start_at=start_at,
            status=BookingStatus.pending,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def set_status(self, booking: Booking, status: BookingStatus) -> None:
        booking.status = status
        await self.session.flush()

    async def due_for_reminder(self, now: datetime, until: datetime) -> list[Booking]:
        """Подтверждённые брони, которым пора слать напоминание."""
        result = await self.session.execute(
            select(Booking)
            .options(joinedload(Booking.service))
            .where(
                Booking.status == BookingStatus.confirmed,
                Booking.reminder_sent.is_(False),
                Booking.start_at > now,
                Booking.start_at <= until,
            )
        )
        return list(result.scalars().all())

    async def mark_reminded(self, booking: Booking) -> None:
        booking.reminder_sent = True
        await self.session.flush()
