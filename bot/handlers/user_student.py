"""Модуль обработки команд студента"""
# может не хватать библеотек
from ast import literal_eval
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
from database.model import User,Student,Teacher,Group,TeacherOrNo,Admin
import bot.stater.state as stat
import bot.keys_board.register as reg

async def menu_student (message: Message, state: FSMContext):
    """""
    Функция для вывода меню
    """
    # pylint: disable=C0415:
    from main import bot
    commands = [
        BotCommand(command="/rating", description="Звонки"),
        BotCommand(command="/achievements", description="Рассписание"),
        BotCommand(command="/menu", description="Меню")
    ]
    await bot.set_my_commands(commands)
    await message.answer("Меню возможностей",reply_markup=stu.Student_menu)

async def discipline_schedule (message: Message):
    """Отправка расписания"""
    # написать запрос для вывода расписания
    pass

async def call_schedule (message: Message):
    """Отправка расписания"""
    # написать запрос для вывода расписания
    pass