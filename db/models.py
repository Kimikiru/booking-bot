"""ORM-модели. Менять существующие поля — только по согласованию."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"        # ждёт подтверждения админом
    confirmed = "confirmed"    # подтверждена
    rejected = "rejected"      # отклонена админом
    cancelled = "cancelled"    # отменена клиентом


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Service {self.id} {self.title!r}>"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), nullable=False, default=BookingStatus.pending, index=True
    )
    reminder_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    service: Mapped["Service"] = relationship(back_populates="bookings", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Booking {self.id} user={self.user_id} {self.status.value}>"


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[str] = mapped_column(String(256), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PortfolioItem {self.id} pos={self.position}>"
