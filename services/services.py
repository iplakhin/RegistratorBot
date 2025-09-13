from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import db.db
from db.db import *
from lexicon.lexicon import LEXICON
from keyboard.keyboards import user_appointments_list_kb


def get_calendar_markup(month_shift: int = 0) -> InlineKeyboardMarkup:
    now = datetime.now()
    first_day_of_current_month = now.replace(day=1)

    # Смещаем на нужный месяц
    target_month = first_day_of_current_month + relativedelta(months=month_shift)

    # Запрещаем листать раньше текущего месяца
    if target_month < first_day_of_current_month:
        target_month = first_day_of_current_month
        month_shift = 0

    month_days = calendar.monthcalendar(target_month.year, target_month.month)

    kb = []

    # Заголовок с месяцем и годом
    month_name = calendar.month_name[target_month.month]
    header_button = InlineKeyboardButton(text=f"{month_name} {target_month.year}", callback_data="ignore")
    kb.append([header_button])

    # Клавиши дней месяца
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_obj = datetime(target_month.year, target_month.month, day)
                # Для текущего месяца скрываем прошедшие даты
                if (target_month.year == now.year and target_month.month == now.month and date_obj.date() < now.date()):
                    row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                else:
                    date_str = date_obj.strftime("%d-%m-%Y")
                    row.append(InlineKeyboardButton(text=str(day), callback_data=f"calendar:{date_str}"))
        kb.append(row)

    # Кнопки навигации
    nav_buttons = []
    if target_month > first_day_of_current_month:
        nav_buttons.append(InlineKeyboardButton(text="<<", callback_data=f"calendar:shift:{month_shift - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=">>", callback_data=f"calendar:shift:{month_shift + 1}"))
    kb.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=kb)

async def get_timeslots_kb(selected_date: datetime) -> InlineKeyboardMarkup:
    timeslots = await get_available_timeslots(selected_date)
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if not timeslots:
        print("Таймслоты вернулись пустыми")
        return kb


    for timeslot in timeslots:
        # Проверяем только если выбран текущий день недели
        slot_time = datetime.strptime(timeslot.start_time, "%H:%M").replace(
            year=selected_date.year, month=selected_date.month, day=selected_date.day
        )

        if selected_date.date() == datetime.now().date():
            if slot_time <= datetime.now() + timedelta(hours=1):
                continue

        button = InlineKeyboardButton(
            text=timeslot.start_time,
            callback_data=f"timeslot_id:{timeslot.id}"
        )
        kb.inline_keyboard.append([button])

    return kb

async def save_appointment(appointment: dict) -> str:
    current_user = await get_or_create_user(appointment["user_id"])

    appointments_list = await db.db.get_user_appointments(current_user.id)

    timeslot = await get_timeslot_by_id(appointment["selected_timeslot_id"])

    is_primary_appointment = False if len(appointments_list) > 0 else True
    print(is_primary_appointment)

    if await is_timeslot_available(appointment_date=datetime.strptime(appointment["selected_date"], "%d-%m-%Y").date(),
                                   timeslot_pk=appointment["selected_timeslot_id"]):
        created_appointment = None
        return f"Вы записаны к доктору\n{created_appointment.__str__()} часов"
    else:
        return "К сожалению выбранное время уже занято.\nВыберите другое"

async def get_user_appointments(user_telegram_id: int) -> InlineKeyboardMarkup:
    user = await get_or_create_user(user_telegram_id)
    if user:
        appointments_list = await db.db.get_user_appointments(user_pk=user.id)
    else:
        raise ValueError("User is not found")

    if appointments_list is not None:
        if len(appointments_list) > 0:
           return user_appointments_list_kb(appointments_list)

    return InlineKeyboardMarkup(inline_keyboard=[])




