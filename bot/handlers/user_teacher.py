"""Модуль обработки команд Преподователя"""
# может не хватать библеотек
from peewee import IntegrityError
from aiogram import Bot
from aiogram.types import Message,CallbackQuery,BotCommand
from aiogram.fsm.context import FSMContext
import bot.keys_board.teacher as tea
from bot.state.state import User

async def menu_teacher(message:Message,state:FSMContext,bot: Bot) -> None:
    """""
    Функция для вывода меню
    """
    await state.clear()
    await message.answer("Меню возможностей",reply_markup=tea.Teach_menu)
    from main import bot
    commands = [
        BotCommand(command="/add_achivment", description="Создать достижение"),
        BotCommand(command="/add_to_user", description="Отправить достижение"),
        BotCommand(command="/menu", description="Меню")
    ]
    await bot.set_my_commands(commands)

async def discipline_schedule (message: Message):
    """Отправка расписания"""
    # написать запрос для вывода расписания ОДНОЙ дисциплины
    pass

async def call_schedule (message: Message):
    """Отправка расписания"""
    # написать запрос для вывода расписания
    pass