"""Портфолио: фото-галерея из БД с листанием ← →."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.portfolio import PortfolioRepository
from keyboards.callbacks import NavCB, PortfolioCB
from keyboards.common import main_menu_kb
from keyboards.portfolio import gallery_kb

logger = logging.getLogger(__name__)
router = Router(name="portfolio")


def _caption(caption: str | None) -> str:
    return caption or "Из наших работ"


@router.callback_query(NavCB.filter(F.to == "portfolio"))
async def open_portfolio(callback: CallbackQuery, session: AsyncSession) -> None:
    repo = PortfolioRepository(session)
    total = await repo.count_active()
    if total == 0:
        await callback.answer()
        if isinstance(callback.message, Message):
            await callback.message.answer(
                "Портфолио пока пустое, скоро добавим работы 🙌",
                reply_markup=main_menu_kb(),
            )
        return

    item = await repo.get_by_offset(0)
    if isinstance(callback.message, Message):
        await callback.message.answer_photo(
            photo=item.file_id,
            caption=_caption(item.caption),
            reply_markup=gallery_kb(0, total),
        )
    await callback.answer()


@router.callback_query(PortfolioCB.filter())
async def navigate(
    callback: CallbackQuery, callback_data: PortfolioCB, session: AsyncSession
) -> None:
    repo = PortfolioRepository(session)
    total = await repo.count_active()
    offset = max(0, min(callback_data.offset, total - 1))

    item = await repo.get_by_offset(offset)
    if item is None:
        await callback.answer("Работа не найдена", show_alert=True)
        return

    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=item.file_id, caption=_caption(item.caption)),
                reply_markup=gallery_kb(offset, total),
            )
        except TelegramBadRequest:
            # Например, «message is not modified» при повторном тапе — не критично.
            pass
    await callback.answer()
