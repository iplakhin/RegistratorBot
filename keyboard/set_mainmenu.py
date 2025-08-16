
from aiogram import Bot
from aiogram.types import BotCommand
from lexicon.lexicon import MAIN_MENU_COMMANDS


async def set_main_menu(bot: Bot) -> None:
    mainmenu_commands = [BotCommand(command=command, description=description)
                         for command, description in MAIN_MENU_COMMANDS.items()]
    await bot.set_my_commands(mainmenu_commands)
