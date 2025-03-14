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
    keyboard= InlineKeyboardBuilder()
    data = await service.get_request('/groups/')
    groups = data.get("entities", [])
    for group in groups:
        group_name = group.get("name")
        if group_name: 
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