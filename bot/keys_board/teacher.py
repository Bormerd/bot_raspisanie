"""Библеотека для создания кнопок Преподавателя"""
# может не хватать библеотек
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton,InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


Teacher_menu = ReplyKeyboardMarkup(keyboard = [
    [
    KeyboardButton(text = 'Звонки'),
    KeyboardButton(text = 'Рассписание'),
    ]])
