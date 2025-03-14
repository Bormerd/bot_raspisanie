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
    """Функция для вывода кнопок дисциплин"""
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

async def user_discipline(chat_id):
    """Функция для вывода кнопок дисциплин пользователя"""
    keyboard = InlineKeyboardBuilder()
    user_response = await service.get_request(f'/user/{chat_id}/')
    disciplines_response = await service.get_request(f'/disciplines/')
    disciplines = disciplines_response.get("entities", [])
    teacher_discipline_ids = user_response.get("id", [])
    if not teacher_discipline_ids:
        return None 
    for discipline in disciplines:
        if discipline.get("id") in teacher_discipline_ids:
            discipline_name = discipline.get("name")
            if discipline_name:
                keyboard.add(
                    InlineKeyboardButton(
                        text=discipline_name,
                        callback_data=f'discipline_{discipline.get("id")}'
                        )
                    )
    keyboard.adjust(4)
    return keyboard.as_markup(),len(teacher_discipline_ids)
