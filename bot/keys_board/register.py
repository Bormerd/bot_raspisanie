"""Модуль обработки регистраций"""
# может не хватать библеотек
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
import aiohttp
Keyboard_register = InlineKeyboardMarkup(inline_keyboard=[
    [
    InlineKeyboardButton(text="Преподаватель", callback_data='Преподаватель'),
    InlineKeyboardButton(text="Студент", callback_data='Студент')
    ]])
FASTAPI_URL = 'http://localhost:8000'
async def group():
    """Функция для вывода кнопок с группами"""
    i = False
    
    keyboard = InlineKeyboardMarkup(row_width=4)  # Устанавливаем ширину строки в 4 кнопки
    async with aiohttp.ClientSession() as session:
        async with session.get(FASTAPI_URL + '/groups/') as response:
            if response.status == 200:
                data = await response.json()  # Получаем данные в формате JSON
                groups = data.get("entities", [])  # Извлекаем список групп из поля "entities"
                
                if not groups:
                    print("Нет доступных групп")
                    return keyboard  # Возвращаем пустую клавиатуру, если групп нет
                
                for group in groups:
                    keyboard.add(InlineKeyboardButton(
                        text=f"{group['name']}",
                        callback_data=f'group_{group["name"]}'
                    ))
                i = True
            else:
                print("Ошибка при получении групп")
    if i:
        return keyboard
    return i

async def discipline(FASTAPI_URL):
    """Функция для вывода кнопок с группами"""
    keyboard = InlineKeyboardMarkup(row_width=4)
    i = False
    async with aiohttp.ClientSession() as session:
            async with session.get(FASTAPI_URL + '/disciplines/') as response:
                if response.status == 200:
                    disciplines = await response.json()
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