"""Точка входа: сборка бота, DI, планировщик, запуск polling."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_settings
from db.base import create_engine, create_session_factory, init_models
from handlers import setup_routers
from middlewares.db import DbSessionMiddleware
from services.reminder import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot")


async def main() -> None:
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # БД
    engine = create_engine()
    await init_models(engine)
    session_pool = create_session_factory(engine)

    # DI: settings доступны в хендлерах как аргумент `settings`
    dp["settings"] = settings

    # Сессия БД — на каждый апдейт (message и callback_query)
    session_mw = DbSessionMiddleware(session_pool)
    dp.message.middleware(session_mw)
    dp.callback_query.middleware(session_mw)

    dp.include_router(setup_routers())

    # Фоновые напоминания
    scheduler = setup_scheduler(bot, session_pool, settings)
    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен (polling). Часовой пояс: %s", settings.tz)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Выход по сигналу")
