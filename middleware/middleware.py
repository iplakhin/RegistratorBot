from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any

ALLOWED_USERS = [544312899,361046129]  # Telegram ID пользователей с доступом

class PermissionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        user = event.message.from_user if event.message else event.callback_query.from_user
        if user.id not in ALLOWED_USERS:
            await event.answer("У вас нет доступа к этому боту.") if hasattr(event, 'answer') else await event.message.answer("У вас нет доступа.")
            return
        return await handler(event, data)