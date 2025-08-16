import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import settings
from handlers import handlers
from keyboard.set_mainmenu import set_main_menu
from middleware.middleware import PermissionMiddleware


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main() -> None:
    logging.basicConfig(
        level=logging.getLevelName(level=settings.log.level),
        format=settings.log.format,
    )

    bot: Bot = Bot(token=settings.bot.token, parse_mode="HTML")
    storage: MemoryStorage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)


    await set_main_menu(bot)
    dp.include_router(handlers.router)
    dp.update.outer_middleware(PermissionMiddleware())
    #dp.callback_query.middleware(RegistrationCheck)
    #dp.message.middleware(PermissionCheck)
    #dp.callback_query.middleware(PermissionCheck)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())




