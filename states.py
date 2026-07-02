"""FSM-состояния бота."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BookingSG(StatesGroup):
    """Сценарий записи: услуга → дата → слот → телефон → подтверждение."""

    service = State()
    date = State()
    slot = State()
    phone = State()
    confirm = State()
