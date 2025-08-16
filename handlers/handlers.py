from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import get_or_create_user
from db.models.models import Appointment
from services.services import get_calendar_markup, get_timeslots_kb, get_user_appointments, save_appointment, cancel_appointment

router = Router()

class BookingState(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    entering_name_and_phone = State()

class CancelState(StatesGroup):
    choosing_appointment = State()
    confirming_cancel = State()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await get_or_create_user(message.from_user.id)
    await message.answer("Добро пожаловать! Для записи на прием выберите дату:", reply_markup=get_calendar_markup())
    await state.set_state(BookingState.choosing_date)

@router.callback_query(F.data.startswith("calendar:"), BookingState.choosing_date)
async def select_date(callback: CallbackQuery, state: FSMContext):
    action, payload = callback.data.split(":", 1)

    if payload.startswith("shift:"):
        # Навигация по календарю
        month_shift = int(payload.split(":")[1])
        markup = get_calendar_markup(month_shift)
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    else:
        await state.update_data(selected_date=payload)

        # Получаем день недели выбранной даты (0 = Пн, 6 = Вс)
        weekday = datetime.strptime(payload, "%d-%m-%Y").weekday()
        await state.update_data(weekday=weekday)
        # Получаем клавиатуру временных слотов
        timeslots_kb = await get_timeslots_kb(datetime.strptime(payload, "%d-%m-%Y"))

        if isinstance(timeslots_kb, str):
            text = f"Вы выбрали дату: {payload}\n{timeslots_kb}"
            await callback.message.edit_text(text)
        else:
            text = f"Вы выбрали дату: {payload}\nТеперь выберите время:"
            await callback.message.edit_text(text, reply_markup=timeslots_kb)

        await callback.answer()
        await state.set_state(BookingState.choosing_time)

@router.callback_query(F.data.startswith("time:"), BookingState.choosing_time)
async def select_time(callback: CallbackQuery, state: FSMContext):
    time = callback.data.split(":")[1]
    await state.update_data(selected_time=time)
    await callback.message.edit_text(f"Вы выбрали время: {time}\nВведите ваше имя и номер телефона для связи")
    await state.set_state(BookingState.entering_name_and_phone)
    await callback.answer()

@router.message(BookingState.entering_name_and_phone)
async def process_name_and_phone(message: Message, state: FSMContext):
    await state.update_data(user_data=message.text)
    data = await state.get_data()
    appointment = {
        "user_id": message.from_user.id,
        "selected_date": data["selected_date"],
        "selected_time": data["selected_time"],
        "weekday": data["weekday"],
        "user_data": data["user_data"]
    }
    response = await save_appointment(appointment)

    await message.answer(response)
    await state.clear()

@router.message(F.text == "/appointments")
async def show_appointments(message: Message, state: FSMContext):
    await state.clear()
    records = get_user_appointments(message.from_user.id)
    if records:
        text = "\n\n".join([f"{r['date']} {r['time']} — {r['name']} ({r['phone']})" for r in records]) # тут возвращаем клавиатуру с записями
    else:
        text = "У вас пока нет записей."
    await message.answer(text)
    await state.set_state(CancelState.choosing_appointment)

@router.message(F.text == "/cancel")
async def cancel_menu(message: Message):
    records = get_user_appointments(message.from_user.id)
    if not records:
        await message.answer("У вас нет записей.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{r['date']} {r['time']}", callback_data=f"cancel:{r['id']}")] for r in records
    ])
    await message.answer("Выберите запись для отмены:", reply_markup=kb)

@router.callback_query(F.data.startswith("cancel:"))
async def process_cancel(callback: CallbackQuery):
    appointment_id = callback.data.split(":")[1]
    cancel_appointment(appointment_id)
    await callback.message.edit_text("Запись отменена.")
    await callback.answer()

@router.callback_query()
async def other(message: Message):
    pass
