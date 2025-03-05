"""Модуль обработки команд"""
# может не хватать библеотек
from aiogram.filters import CommandStart
from aiogram import Dispatcher, F
import bot.handlers.register as reg
import bot.state.state as stat
from RequestsUrl import AddressService
import bot.handlers.user_student as stu
import bot.handlers.user_teacher as tea
import bot.filters.cheak as cheak

def function(dp:Dispatcher):
    """"Регистрация команд"""
    dp.callback_query.register(reg.register_ending,stat.User.reg_end)
    dp.callback_query.register(reg.teacher_register,F.data == "Преподаватель")
    dp.callback_query.register(reg.student_register,F.data == "Студент")
    dp.message.register(reg.command_start_handler, CommandStart())
    dp.message.register(stu.menu_student, F.text == '/menu', cheak.CheakStudent())
    dp.message.register(stu.discipline_schedule, F.text == '/schedule', cheak.CheakStudent())