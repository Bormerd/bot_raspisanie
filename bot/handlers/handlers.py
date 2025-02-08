"""Модуль обработки команд"""
# может не хватать библеотек
from aiogram.filters import CommandStart
from aiogram import Dispatcher,F
import bot.handlers.register as reg
import bot.handlers.admin as adm
import bot.stater.state as stat
import bot.filters.cheak as cheak
from database.model import start_db

def function(dp:Dispatcher):
    """"Регистрация команд"""
    # переписать команды 
    # dp.callback_query.register(reg.not_teach,F.data.startswith ('name_'))
    # dp.callback_query.register(reg.teacher_registr,F.data.startswith ('name1_'))
    # dp.callback_query.register(reg.teacher_confirmed,F.data=='Преподаватель')
    # dp.callback_query.register(reg.student_registr,F.data== 'Студент')
    # dp.callback_query.register(reg.sudent_groops,stat.USR.Groops)
    # dp.callback_query.register(adm.group_edu_add,stat.USR.group_add)
    # dp.message.register(reg.command_start_handler, CommandStart())
    # dp.message.register(reg.name_user,stat.USR.name)
    # dp.message.register(adm.menu_admin,F.text == "/menu",cheak.Cheakadmin())
    # dp.message.register(adm.group_add,F.text == "/group",cheak.Cheakadmin())
    # dp.message.register(adm.group_name,stat.USR.group_name_add)
    # dp.message.register(adm.edu_add,F.text == "/edu_add",cheak.Cheakadmin())
    # dp.message.register(adm.edu_name,stat.USR.edu_add)