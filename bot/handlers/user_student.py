"""Модуль обработки команд студента"""
# может не хватать библиотек
from ast import literal_eval
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram import F
import bot.state.state as stat
import bot.keys_board.register as reg
from RequestsUrl import service
from aiogram.types import BotCommand
import bot.keys_board.student as stu

async def menu_student(message: Message):
    """Функция для вывода меню"""
    # pylint: disable=C0415:
    from main import bot
    commands = [
        BotCommand(command="/rating", description="Звонки"),
        BotCommand(command="/schedule", description="Расписание"),
        BotCommand(command="/menu", description="Меню")
    ]
    await bot.set_my_commands(commands)
    await message.answer("Меню возможностей", reply_markup=stu.Student_menu)

async def discipline_schedule(message: Message):
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
        # Исправлено: используем двойные фигурные скобки для экранирования
        schedule_details_response = await service.get_request(f'/schedule/{schedule_id}/?group_id={group_id["__data__"]["id"]}')
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
            await message.answer(message_text, parse_mode="HTML")

async def send_bells_photo(message: Message):
    """Отправка фотографии с расписанием звонков"""
    photo = FSInputFile("Звонки.png")  
    await message.answer_photo(photo, caption="Расписание звонков")

async def handle_text_message(message: Message):
    """Обработка текстовых сообщений"""
    text = message.text.lower()  
    
    if text == "расписание":
        await discipline_schedule(message) 
    elif text == "Звонки":
        await send_bells_photo(message)  
    else:
        await message.answer("Неизвестная команда. Используйте /menu для вызова меню.")