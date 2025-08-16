from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import get_or_create_user
from db.models.models import Appointment
from services.services import get_calendar_markup, get_timeslots_kb, get_user_appointments, save_appointment, cancel_appointment
from lexicon.lexicon import MAIN_MENU_COMMANDS, LEXICON


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
    await message.answer(LEXICON["start_message"])

@router.message(F.text == "/zapis")
async def make_appointment(message: Message, state: FSMContext):
    await message.answer(LEXICON["select_date"], reply_markup=get_calendar_markup())
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

        if not timeslots_kb:
            await callback.message.edit_text(LEXICON["no_timeslots"])
        else:
            text = f"Вы выбрали дату: {payload}\nТеперь выберите время"
            await callback.message.edit_text(text=text, reply_markup=timeslots_kb)

        await state.set_state(BookingState.choosing_time)

@router.callback_query(F.data.startswith("timeslot_id:"), BookingState.choosing_time)
async def select_time(callback: CallbackQuery, state: FSMContext):
    timeslot_id = int(callback.data.split(":")[1])
    await state.update_data(selected_timeslot_id=timeslot_id)
    await callback.message.edit_text(LEXICON["input_fio_tel"])
    await state.set_state(BookingState.entering_name_and_phone)
    await callback.answer()

@router.message(BookingState.entering_name_and_phone)
async def process_name_and_phone(message: Message, state: FSMContext):
    await state.update_data(user_data=message.text)
    data = await state.get_data()
    appointment = {
        "user_id": message.from_user.id,
        "selected_date": data["selected_date"],
        "selected_timeslot_id": data["selected_timeslot_id"],
        "weekday": data["weekday"],
        "user_data": data["user_data"]
    }
    response = await save_appointment(appointment)

    await message.answer(text=LEXICON["appointment_success"] + "\n" + response)
    await state.clear()

@router.message(F.text == "/moi_zapisi")
async def show_appointments(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = await get_user_appointments(callback.from_user.id)
    if not kb.inline_keyboard:
        await callback.answer("Вы еще не записаны к доктору")
    else:
        await callback.answer(text="Ваши записи\nНажмите на запись чтобы отменить или перенести", reply_markup=kb)

@router.message(F.text == "/otmena")
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
