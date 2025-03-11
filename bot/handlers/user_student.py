from datetime import datetime
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram import F
from RequestsUrl import service
from aiogram.types import BotCommand
from bot.keys_board.student import get_dates_keyboard, Student_menu

async def menu_student(message: Message):
    """Функция для вывода меню"""
    commands = [
        BotCommand(command="/rating", description="Звонки"),
        BotCommand(command="/schedule", description="Расписание"),
        BotCommand(command="/menu", description="Меню")
    ]
    await message.bot.set_my_commands(commands)
    
    # Выводим основное меню
    await message.answer("Меню возможностей", reply_markup=Student_menu)

async def discipline_schedule(message: Message):
    """Отправка расписания на все дни"""
    schedules_response = await service.get_request('/schedules/')
    if schedules_response is None:
        await message.answer("Ошибка при получении списка расписаний.")
        return
    
    schedules = schedules_response.get("entities", [])
    group_response = await service.get_request(f'/user/{message.chat.id}/')
    if group_response is None:
        await message.answer("Ошибка при получении информации о пользователе.")
        return
    
    group_id = group_response.get("id")
    group = group_response  # Предполагаем, что group_response — это словарь
    
    if not schedules:
        await message.answer("Нет доступных расписаний.")
        return
    
    for schedule in schedules:
        schedule_id = schedule.get("id")
        # Исправлено: используем двойные фигурные скобки для экранирования
        schedule_details_response = await service.get_request(f'/schedule/{schedule_id}/?group_id={group_id["__data__"]["id"]}')
        if schedule_details_response is None:
            continue  # Пропускаем, если расписание не найдено
        
        schedule_details = schedule_details_response.get("entities", [])
        date = await service.get_request(f'/date/{schedule_id}')
        if date is None:
            continue  # Пропускаем, если дата не найдена
        
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
        
async def get_schedule_by_date(message: Message, state: FSMContext):
    """Получение расписания по конкретной дате"""
    date_str = message.text.replace("Расписание на ", "").strip()
    
    # Проверка, что введенный текст является датой
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД.")
        return
    
    try:
        # Получаем список всех расписаний
        schedules_response = await service.get_request('/schedules/')
        if schedules_response is None:
            await message.answer("Ошибка при получении списка расписаний.")
            return
        
        schedules = schedules_response.get("entities", [])
        
        # Проверяем, есть ли введенная дата в списке расписаний
        date_exists = any(schedule.get("date") == date_str for schedule in schedules)
        
        if not date_exists:
            await message.answer(f"На дату {date_str} расписания нет.")
            return
        
        # Получаем информацию о пользователе
        group_response = await service.get_request(f'/user/{message.chat.id}/')
        if group_response is None:
            await message.answer("Ошибка при получении информации о пользователе.")
            return
        
        group_id = group_response.get("id")
        
        # Проверяем, что group_id - это число
        if isinstance(group_id, dict) and "__data__" in group_id:
            group_id = group_id["__data__"]["id"]
        
        # Запрашиваем расписание на конкретную дату
        schedule_response = await service.get_request(f'/schedule/date/{date_str}/?group_id={group_id}')
        
        # Если API возвращает None (404), значит расписание на эту дату отсутствует
        if schedule_response is None:
            await message.answer(f"На дату {date_str} расписания для вашей группы нет.")
            return
        
        schedule_details = schedule_response.get("entities", [])
        
        if not schedule_details:
            await message.answer(f"На дату {date_str} расписания для вашей группы нет.")
            return
        
        # Формируем сообщение с расписанием
        message_text = f"Расписание на {date_str}:\n"
        for detail in schedule_details:
            discipline = detail.get("discipline", {}).get("name", "Неизвестно")
            auditory = detail.get("auditory", {}).get("name", "Неизвестно")
            pair = detail.get("pair")
            message_text += f"<b>{pair}) {discipline} ({auditory})</b>\n"
        
        await message.answer(message_text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Ошибка при получении расписания: {e}")

async def send_bells_photo(message: Message):
    """Отправка фотографии с расписанием звонков"""
    try:
        photo = FSInputFile("Звонки.png")
        await message.answer_photo(photo, caption="Расписание звонков")
    except Exception as e:
        await message.answer(f"Ошибка при отправке фотографии: {e}")

async def handle_text_message(message: Message, state: FSMContext):
    """Обработка текстовых сообщений"""
    text = message.text.lower()
    
    if text == "звонки":
        await send_bells_photo(message)
    elif text == "расписание на все дни":
        await discipline_schedule(message)
    elif text == "расписание на конкретный день":
        dates_keyboard = await get_dates_keyboard()
        await message.answer("Выберите дату для просмотра расписания:", reply_markup=dates_keyboard)
    elif text.startswith("расписание на"):
        date = text.replace("расписание на", "").strip()
        await state.update_data(selected_date=date)
        await get_schedule_by_date(message, state)
    elif text == "назад": 
        await menu_student(message) 
    else:
        await message.answer("Неизвестная команда. Используйте /menu для вызова меню.")