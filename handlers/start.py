"""Стартовый роутер — эталон паттерна: тонкие хендлеры, логика снаружи.

Здесь же живут глобальные команды /start и /cancel: /cancel чистит FSM
с любого шага любого сценария.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from keyboards.callbacks import NavCB
from keyboards.common import main_menu_kb

logger = logging.getLogger(__name__)
router = Router(name="start")

GREETING = (
    "👋 <b>Здравствуйте!</b>\n\n"
    "Я помогу записаться на приём и покажу примеры наших работ.\n"
    "Выберите, что нужно:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(GREETING, reply_markup=main_menu_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Нечего отменять. Открываю меню:", reply_markup=main_menu_kb())
    else:
        # Сначала убираем возможную reply-клавиатуру (шаг с контактом), потом меню.
        await message.answer("Отменено. Возвращаемся в меню.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(NavCB.filter(F.to == "menu"))
async def to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await callback.message.answer(GREETING, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    """Кнопка-счётчик в галерее — просто гасим «часики»."""
    await callback.answer()
