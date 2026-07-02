"""Глобальный перехват ошибок: логируем и мягко сообщаем пользователю.

Хендлер не «глотает» баг молча — стектрейс уходит в лог, а юзер получает
понятное сообщение вместо зависшего сценария.
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)
router = Router(name="errors")

USER_MESSAGE = "Упс, что-то пошло не так 😞 Попробуйте ещё раз или наберите /start"


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    logger.exception("Необработанная ошибка при обработке апдейта", exc_info=event.exception)

    update = event.update
    try:
        if update.message is not None:
            await update.message.answer(USER_MESSAGE)
        elif update.callback_query is not None:
            await update.callback_query.answer(USER_MESSAGE, show_alert=True)
    except Exception:
        logger.exception("Не удалось отправить пользователю сообщение об ошибке")

    return True  # ошибка обработана — дальше не всплывает
