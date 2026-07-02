"""Конфигурация приложения. Все секреты и настройки — только из .env / окружения."""
from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Обязательные секреты
    bot_token: str
    admin_id: int

    # Инфраструктура
    database_url: str = "sqlite+aiosqlite:///bot.db"

    # Бизнес-настройки записи
    work_start_hour: int = 10          # начало рабочего дня (час)
    work_end_hour: int = 19            # конец рабочего дня (час)
    booking_horizon_days: int = 14     # на сколько дней вперёд открыта запись
    reminder_before_hours: int = 2     # за сколько часов напоминать клиенту
    tz: str = "Europe/Moscow"          # часовой пояс бизнеса

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


@lru_cache
def get_settings() -> Settings:
    """Настройки читаются один раз и кэшируются."""
    return Settings()  # type: ignore[call-arg]
