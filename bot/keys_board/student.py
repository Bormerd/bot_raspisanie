"""Библеотека для создания кнопок студента"""
# может не хватать библеотек
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton

Student_menu = ReplyKeyboardMarkup(keyboard = [
[
    KeyboardButton(text = 'Звонки'), KeyboardButton(text = 'Расписание')
]])