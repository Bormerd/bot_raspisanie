"""Библеотека для создания кнопок Преподавателя"""
# может не хватать библеотек
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton,InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from RequestsUrl import service

Teacher_menu = ReplyKeyboardMarkup(keyboard = [
    [
    KeyboardButton(text = 'добавить дисциплину'),
    KeyboardButton(text = 'Рассписание'),
    KeyboardButton(text = 'Удалить дисциплину'),
    KeyboardButton(text = 'Меню')
    ]])

async def discipline():
    """Функция для вывода кнопок с группами"""
    keyboard= InlineKeyboardBuilder()
    data = await service.get_request('/disciplines/')
    disciplines = data.get("entities", [])
    for disciplines in disciplines:
        disciplines_name = disciplines.get("name")
        if disciplines_name:
            keyboard.add(
                InlineKeyboardButton(
                    text=disciplines_name,
                    callback_data=f'disciplines_{disciplines_name}'
                )
            )
    keyboard.adjust(4)
    return keyboard.as_markup()