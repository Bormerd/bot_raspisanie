"""Модуль обработки команд студента"""
# может не хватать библеотек
from ast import literal_eval
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.state.state as stat
import bot.keys_board.register as reg
from RequestsUrl import service
from aiogram.types import BotCommand
import bot.keys_board.student as stu

async def menu_student (message: Message):
    """""
    Функция для вывода меню
    """
    # pylint: disable=C0415:
    from main import bot
    commands = [
        BotCommand(command="/rating", description="Звонки"),
        BotCommand(command="/schedule", description="Рассписание"),
        BotCommand(command="/menu", description="Меню")
    ]
    await bot.set_my_commands(commands)
    await message.answer("Меню возможностей",reply_markup=stu.Student_menu)

async def discipline_schedule (message: Message):
    """Отправка расписания"""
    schedules_response = await service.get_request('/schedules/')
    schedules = schedules_response.get("entities", [])
    group_response = await service.get_request(f'/user/{message.chat.id}/')
    group_id = group_response.get("id")
    group = group_response  # Предполагаем, что group_response — это словарь
    if not schedules:
        await message.answer("Нет доступных расписаний.")
        return
    
    for schedule in schedules:
        schedule_id = schedule.get("id")
        schedule_details_response = await service.get_request(f'/schedule/{schedule_id}/?group_id={group_id['__data__']['id']}')
        schedule_details = schedule_details_response.get("entities", [])
        date = await service.get_request(f'/date/{schedule_id}')
        if schedule_details:
            message_text = ""
            for detail in schedule_details:
                discipline = detail.get("discipline", {}).get("name", "Неизвестно")
                auditory = detail.get("auditory", {}).get("name", "Неизвестно")
                pair = detail.get("pair")
                message_text += f"<b>{pair}) {discipline} ({auditory})</b>\n"
            else:
                message_text += f"\nДата: <code>{date['date']}</code>"
            # message_text = message_text.strip()
            await message.answer(message_text, parse_mode="HTML")

async def call_schedule (message: Message):
    """Отправка расписания звонков"""
    # написать запрос для вывода звонков
    pass