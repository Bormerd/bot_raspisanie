"""Библиотека для создания кнопок студента"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from RequestsUrl import service

async def get_dates_keyboard():
    """Получение клавиатуры с датами"""
    try:
        # Запрашиваем расписания из базы данных
        schedules_response = await service.get_request('/schedules/')
        schedules = schedules_response.get("entities", [])
        
        # Извлекаем уникальные даты и сортируем их
        dates = list(set([schedule.get("date") for schedule in schedules]))
        dates.sort()
        
        # Формируем кнопки с датами
        keyboard = [
            [KeyboardButton(text=f"Расписание на {date}")] for date in dates
        ]
        keyboard.append([KeyboardButton(text="Назад")])
        
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    except Exception as e:
        print(f"Ошибка при получении дат: {e}")
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)

# Основное меню студента
Student_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Звонки'), KeyboardButton(text='Расписание на все дни')],
    [KeyboardButton(text='Расписание на конкретный день')]
], resize_keyboard=True)