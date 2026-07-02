"""Сборка всех per-feature роутеров в один."""
from aiogram import Router

from handlers import admin, booking, errors, portfolio, start


def setup_routers() -> Router:
    root = Router()
    # Порядок важен: сначала общие/стартовые, потом фичи.
    root.include_router(errors.router)
    root.include_router(start.router)
    root.include_router(booking.router)
    root.include_router(portfolio.router)
    root.include_router(admin.router)
    return root
