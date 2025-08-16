from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def mock_appointments_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Запись 1 (12.07 14:00)", callback_data="appointment_1")],
        [InlineKeyboardButton(text="Запись 2 (13.07 16:00)", callback_data="appointment_2")]
    ])

def confirm_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="confirm_cancel")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_appointments")]
    ])