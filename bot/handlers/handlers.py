"""Модуль обработки команд"""
# может не хватать библеотек
from aiogram.filters import CommandStart
from aiogram import Dispatcher, F
import bot.handlers.register as reg
import bot.state.state as stat
from RequestsUrl import AddressService

def function(dp:Dispatcher):
    """"Регистрация команд"""
    # переписать команды
    dp.callback_query.register(reg.register_ending,stat.User.reg_end)
    dp.callback_query.register(reg.teacher_register,F.data == "Пеподаватель")
    dp.callback_query.register(reg.student_register,F.data == "Студент")
    dp.message.register(reg.command_start_handler, CommandStart())