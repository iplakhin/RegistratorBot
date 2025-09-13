from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_appointments_list_kb(appointments_list):
    kb = InlineKeyboardBuilder()
    if appointments_list is not None:
        for appointment in appointments_list:
            button = InlineKeyboardButton(text=appointment.__str__(), callback_data=f"appointment_id:{appointment.id}")
            kb.row(button, width=1)
    else:
        return InlineKeyboardMarkup(inline_keyboard=[])
    return  kb.as_markup()


def confirm_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="confirm_cancel")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_appointments")]
    ])