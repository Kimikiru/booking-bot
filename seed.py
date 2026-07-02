"""Наполнение БД примерами услуг (идемпотентно).

Портфолио наполняется иначе: отправьте боту фото от имени администратора —
оно автоматически попадёт в галерею (см. handlers/admin.py).

Запуск:  python seed.py
"""
from __future__ import annotations

import asyncio
import logging

from db.base import create_engine, create_session_factory, init_models
from db.repositories.service import ServiceRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEMO_SERVICES = [
    ("Консультация", 30, 1000),
    ("Стрижка", 60, 1500),
    ("Окрашивание", 120, 4000),
]


async def main() -> None:
    engine = create_engine()
    await init_models(engine)
    session_pool = create_session_factory(engine)

    async with session_pool() as session:
        repo = ServiceRepository(session)
        existing = await repo.list_active()
        if existing:
            logger.info("Услуги уже есть (%d) — пропускаю сид", len(existing))
        else:
            for title, duration, price in DEMO_SERVICES:
                await repo.add(title=title, duration_min=duration, price=price)
            await session.commit()
            logger.info("Добавлено услуг: %d", len(DEMO_SERVICES))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
