"""Админские действия под заявкой: подтвердить / отклонить."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from db.models import BookingStatus
from db.repositories.booking import BookingRepository
from db.repositories.portfolio import PortfolioRepository
from keyboards.callbacks import AdminCB

logger = logging.getLogger(__name__)
router = Router(name="admin")


async def _notify_client(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
    except Exception:
        logger.exception("Не удалось уведомить клиента %s", user_id)


@router.callback_query(AdminCB.filter())
async def handle_admin_action(
    callback: CallbackQuery,
    callback_data: AdminCB,
    session: AsyncSession,
    settings: Settings,
    bot: Bot,
) -> None:
    if callback.from_user.id != settings.admin_id:
        await callback.answer("Недоступно", show_alert=True)
        return

    repo = BookingRepository(session)
    booking = await repo.get(callback_data.booking_id)
    if booking is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    if booking.status != BookingStatus.pending:
        await callback.answer(f"Заявка уже: {booking.status.value}", show_alert=True)
        return

    when = booking.start_at.strftime("%d.%m.%Y %H:%M")
    if callback_data.action == "confirm":
        await repo.set_status(booking, BookingStatus.confirmed)
        result_line = "✅ Подтверждена"
        await _notify_client(
            bot,
            booking.user_id,
            f"✅ Ваша запись на <b>{when}</b> подтверждена! Напомним заранее.",
        )
    else:  # reject
        await repo.set_status(booking, BookingStatus.rejected)
        result_line = "❌ Отклонена"
        await _notify_client(
            bot,
            booking.user_id,
            f"К сожалению, запись на <b>{when}</b> не подтверждена. "
            "Попробуйте выбрать другое время или свяжитесь с нами.",
        )

    # Обновляем сообщение у админа: убираем кнопки, дописываем итог.
    if isinstance(callback.message, Message) and callback.message.text:
        try:
            await callback.message.edit_text(
                f"{callback.message.text}\n\n<b>{result_line}</b>", reply_markup=None
            )
        except TelegramBadRequest:
            pass
    await callback.answer(result_line)


@router.message(StateFilter(None), F.photo)
async def add_portfolio_photo(
    message: Message, session: AsyncSession, settings: Settings
) -> None:
    """Админ прислал фото вне сценариев → добавляем в портфолио.

    Подпись к фото становится подписью работы. Для обычных пользователей —
    молча игнорируем (нет других обработчиков фото).
    """
    if message.from_user.id != settings.admin_id:
        return
    file_id = message.photo[-1].file_id
    repo = PortfolioRepository(session)
    position = await repo.count_active()
    await repo.add(file_id=file_id, caption=message.caption, position=position)
    await message.answer(
        f"🖼 Добавлено в портфолио (позиция {position + 1}).\n"
        f"<code>file_id</code>: {file_id}"
    )
