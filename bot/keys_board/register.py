"""Модуль обработки регистраций"""
# может не хватать библеотек
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from RequestsUrl import service
import aiohttp

Keyboard_register = InlineKeyboardMarkup(inline_keyboard=[
    [
    InlineKeyboardButton(text="Преподаватель", callback_data='Преподаватель'),
    InlineKeyboardButton(text="Студент", callback_data='Студент')
    ]])

async def group():
    """Функция для вывода кнопок с группами"""
    keyboard= InlineKeyboardBuilder()  # Устанавливаем ширину строки в 4 кнопки
    data = await service.get_request('/groups/')
    groups = data.get("entities", [])
    for group in groups:
        group_name = group.get("name")  # Получаем имя группы
        if group_name:  # Проверяем, что имя группы существует
            keyboard.add(
                InlineKeyboardButton(
                    text=group_name,
                    callback_data=f'group_{group_name}'
                )
            )
    keyboard.adjust(4)
    return keyboard.as_markup()

async def discipline():
    """Функция для вывода кнопок с группами"""
    keyboard = InlineKeyboardMarkup(row_width=4)
    i = False
    disciplines = await service.get_request('/groups/')
    for discipline_name in disciplines:
        keyboard.add(
            InlineKeyboardButton(
                text=discipline_name["discipline_name"],
                callback_data=f'discipline_{discipline_name["discipline_name"]}'
                )
            )
        i = True
    else:
        # Обработка ошибки, если API не доступен
        print("Ошибка при получении дисциплин")
    if i:
        return keyboar
    return i