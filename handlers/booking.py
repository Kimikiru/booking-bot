"""Сценарий записи (FSM): услуга → дата → слот → телефон → подтверждение.

Хендлеры тонкие: вся логика слотов и создания брони — в BookingService.
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from db.repositories.service import ServiceRepository
from keyboards.booking import SLOT_FMT, confirm_kb, dates_kb, services_kb, slots_kb
from keyboards.callbacks import DateCB, NavCB, ServiceCB, SlotCB
from keyboards.common import contact_request_kb, main_menu_kb
from services.booking_service import BookingService, SlotInPastError, SlotTakenError
from services.notifications import notify_admin_new_booking
from states import BookingSG

logger = logging.getLogger(__name__)
router = Router(name="booking")

PHONE_MIN_DIGITS = 5


# --- Шаг 1: выбор услуги ---------------------------------------------------

async def _show_services(message: Message, state: FSMContext, session: AsyncSession) -> bool:
    services = await ServiceRepository(session).list_active()
    if not services:
        await message.answer(
            "Пока нет доступных услуг. Загляните позже 🙏",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return False
    await state.set_state(BookingSG.service)
    await message.answer("Выберите услугу:", reply_markup=services_kb(services))
    return True


@router.callback_query(NavCB.filter(F.to == "book"))
@router.callback_query(NavCB.filter(F.to == "book_service"))
async def open_services(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    if isinstance(callback.message, Message):
        await _show_services(callback.message, state, session)
    await callback.answer()


# --- Шаг 2: выбор даты -----------------------------------------------------

async def _show_dates(message: Message, state: FSMContext, settings: Settings) -> None:
    booking_service = BookingService(None, settings)  # только для дат, БД не нужна
    await state.set_state(BookingSG.date)
    await message.answer(
        "Выберите дату:", reply_markup=dates_kb(booking_service.available_dates())
    )


@router.callback_query(ServiceCB.filter(), BookingSG.service)
async def choose_service(
    callback: CallbackQuery,
    callback_data: ServiceCB,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    service = await ServiceRepository(session).get(callback_data.service_id)
    if service is None or not service.is_active:
        await callback.answer("Услуга недоступна, выберите другую", show_alert=True)
        return
    await state.update_data(service_id=service.id)
    if isinstance(callback.message, Message):
        await _show_dates(callback.message, state, settings)
    await callback.answer()


@router.callback_query(NavCB.filter(F.to == "book_date"), BookingSG.slot)
async def back_to_dates(
    callback: CallbackQuery, state: FSMContext, settings: Settings
) -> None:
    if isinstance(callback.message, Message):
        await _show_dates(callback.message, state, settings)
    await callback.answer()


# --- Шаг 3: выбор слота ----------------------------------------------------

@router.callback_query(DateCB.filter(), BookingSG.date)
async def choose_date(
    callback: CallbackQuery,
    callback_data: DateCB,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    data = await state.get_data()
    service = await ServiceRepository(session).get(data["service_id"])
    if service is None:
        await callback.answer("Услуга недоступна", show_alert=True)
        return

    day = date.fromisoformat(callback_data.value)
    booking_service = BookingService(session, settings)
    slots = await booking_service.free_slots(service, day)

    if not slots:
        await callback.answer("На эту дату свободных слотов нет", show_alert=True)
        return

    await state.update_data(date=day.isoformat())
    await state.set_state(BookingSG.slot)
    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"Свободное время на {day.strftime('%d.%m')}:",
            reply_markup=slots_kb(slots),
        )
    await callback.answer()


# --- Шаг 4: телефон --------------------------------------------------------

@router.callback_query(SlotCB.filter(), BookingSG.slot)
async def choose_slot(
    callback: CallbackQuery, callback_data: SlotCB, state: FSMContext
) -> None:
    await state.update_data(slot=callback_data.value)
    await state.set_state(BookingSG.phone)
    if isinstance(callback.message, Message):
        await callback.message.answer(
            "Оставьте номер телефона для связи — кнопкой ниже или сообщением.\n"
            "Чтобы прервать — /cancel",
            reply_markup=contact_request_kb(),
        )
    await callback.answer()


@router.message(BookingSG.phone, F.contact)
async def phone_from_contact(message: Message, state: FSMContext) -> None:
    await _save_phone_and_confirm(message, state, message.contact.phone_number)


@router.message(BookingSG.phone, F.text)
async def phone_from_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if sum(ch.isdigit() for ch in phone) < PHONE_MIN_DIGITS:
        await message.answer(
            "Это не похоже на номер. Пришлите телефон или нажмите кнопку ниже.",
            reply_markup=contact_request_kb(),
        )
        return
    await _save_phone_and_confirm(message, state, phone)


async def _save_phone_and_confirm(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone, full_name=message.from_user.full_name)
    data = await state.get_data()
    slot_dt = datetime.strptime(data["slot"], SLOT_FMT)
    await state.set_state(BookingSG.confirm)

    summary = (
        "Проверьте заявку:\n\n"
        f"🗓 <b>{slot_dt.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"📱 {phone}\n\n"
        "Отправляем?"
    )
    # Убираем reply-клавиатуру контакта, дальше — inline подтверждение.
    await message.answer("Почти готово 👇", reply_markup=ReplyKeyboardRemove())
    await message.answer(summary, reply_markup=confirm_kb())


# --- Шаг 5: подтверждение и создание брони ---------------------------------

@router.callback_query(F.data == "booking:submit", BookingSG.confirm)
async def submit_booking(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
    bot: Bot,
) -> None:
    data = await state.get_data()
    service = await ServiceRepository(session).get(data["service_id"])
    if service is None:
        await callback.answer("Услуга больше недоступна", show_alert=True)
        await state.clear()
        return

    slot_dt = datetime.strptime(data["slot"], SLOT_FMT)
    booking_service = BookingService(session, settings)
    try:
        booking = await booking_service.create_booking(
            service=service,
            start_at=slot_dt,
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=data.get("full_name"),
            phone=data.get("phone"),
        )
    except SlotTakenError:
        await callback.answer("Это время только что заняли 😔 Выберите другое", show_alert=True)
        await _show_dates(callback.message, state, settings)
        return
    except SlotInPastError:
        await callback.answer("Это время уже прошло. Выберите другое", show_alert=True)
        await _show_dates(callback.message, state, settings)
        return

    # commit сделает middleware после успешного выхода; заявку админу шлём здесь,
    # уже с присвоенным id (после flush внутри репозитория).
    await notify_admin_new_booking(bot, settings.admin_id, booking)
    await state.clear()

    if isinstance(callback.message, Message):
        await callback.message.answer(
            "✅ Заявка отправлена! Мы свяжемся для подтверждения.\n"
            f"Вы записаны на <b>{slot_dt.strftime('%d.%m.%Y %H:%M')}</b>.",
            reply_markup=main_menu_kb(),
        )
    await callback.answer()
