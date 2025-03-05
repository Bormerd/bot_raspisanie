"""Библеотеки для проверки пользователя"""
from aiogram.filters import BaseFilter
from aiogram.types import Message
from RequestsUrl import service

class CheakTeacher(BaseFilter):
    """Проверяет является ли пользователь преподователем"""
    async def __call__ (self, message: Message):
        response = await service.get_request(f'/user/{message.chat.id}/')
        if response and response['type'] == 'teacher':
            return True
        return False

class CheakStudent(BaseFilter):
    """Проверяет является ли пользователь преподователем"""
    async def __call__ (self, message: Message):
        response = await service.get_request(f'/user/{message.chat.id}/')
        if response and response['type'] == 'student':
            return True
        return False