"""CallbackData-фабрики — типизированные callback'и вместо сырых строк."""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class ServiceCB(CallbackData, prefix="svc"):
    service_id: int


class DateCB(CallbackData, prefix="date"):
    value: str  # ISO-дата YYYY-MM-DD


class SlotCB(CallbackData, prefix="slot"):
    value: str  # начало слота, формат %Y%m%dT%H%M


class PortfolioCB(CallbackData, prefix="pf"):
    offset: int  # текущий индекс в галерее (0-based)


class AdminCB(CallbackData, prefix="adm"):
    action: str  # "confirm" | "reject"
    booking_id: int


class NavCB(CallbackData, prefix="nav"):
    to: str  # "menu" | "book" | "portfolio" | "book_service" | "book_date"
