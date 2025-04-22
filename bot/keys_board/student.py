"""Библиотека для создания кнопок студента"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from RequestsUrl import service

async def get_dates_keyboard():
    """Получение клавиатуры с датами в формате ГГГГ-ММ-ДД"""
    try:
        # Запрашиваем расписания из базы данных
        schedules_response = await service.get_request('/schedules/')
        
        if not schedules_response:
            print("Пустой ответ от API")
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)
            
        schedules = schedules_response.get("entities", [])
        
        if not schedules:
            print("Нет данных о расписаниях")
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)
        
        # Извлекаем даты и проверяем их формат
        dates = []
        for schedule in schedules:
            date_str = schedule.get("date")
            if date_str and isinstance(date_str, str):
                # Оставляем дату в исходном формате (предполагая, что API возвращает ГГГГ-ММ-ДД)
                dates.append(date_str)
        
        # Удаляем дубликаты и сортируем
        dates = sorted(list(set(dates)))
        
        # Формируем кнопки с датами в формате ГГГГ-ММ-ДД
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