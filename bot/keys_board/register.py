"""Модуль обработки регистраций"""
# может не хватать библеотек
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup

Keyboard_register = InlineKeyboardMarkup(inline_keyboard=[
    [
    InlineKeyboardButton(text="Преподаватель", callback_data='Преподаватель'),
    InlineKeyboardButton(text="Студент", callback_data='Студент')
    ]])

def group():
    """Функция для вывода кнопок с группами"""
    keyboard = InlineKeyboardBuilder()
    i=False
    group = response.get(FASTAPI_URL+ '/groups/')
    for group_name in group:
        keyboard.add(InlineKeyboardButton(text=f"{group_name["group_name"]}",
            callback_data = f'group_{group_name["group_name"]}'
            ))
        i = True

    if i:
        return keyboard.adjust(2).as_markup()
    return i

def discipline():
    """Функция для вывода кнопок с группами"""
    keyboard = InlineKeyboardBuilder()
    i = False
    discipline = response.get (FASTAPI_URL + '/disciplines/')
    for discipline_name in discipline:

        keyboard.add(InlineKeyboardButton(text=f"{discipline_name["discipline_name"]}",
            callback_data = f'discipline_{discipline_name["discipline_name"]}'
            ))
        i = True

    if i:
        return keyboard.adjust(2).as_markup()
    return i
