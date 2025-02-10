"""Модуль обработки регистраций"""
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.state.state as stat
import bot.keys_board.register as reg
import aiohttp  # Используем aiohttp для асинхронных запросов

FASTAPI_URL = 'http://localhost:8000'

async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start
    Выбор типа пользователя
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(FASTAPI_URL + f'/user/role/{message.chat.id}') as response:
            role = await response.json()
    
    if role:
        await message.answer("Выберите роль", reply_markup=reg.Keyboard_register)
        await state.set_state(stat.User.role)
    else:
        await message.answer(
            f"Вы уже зарегистрированы\n {message.from_user.full_name}, выберите роль",
            reply_markup=reg.Keyboard_register
        )

async def set_role_user(callbak: CallbackQuery, state: FSMContext):
    """Присваивание роли пользователю"""
    await callbak.message.answer("Выберите роль", reply_markup=reg.Keyboard_register)
    role_text = callbak.data  # Предполагаем, что данные кнопки содержат текст роли

    async with aiohttp.ClientSession() as session:
        async with session.post(FASTAPI_URL + '/create/' + str(callbak.message.chat.id), json={"role": role_text}) as response:
            if response.status == 200:
                await callbak.answer("Роль успешно присвоена.")
            else:
                await callbak.answer("Произошла ошибка при присвоении роли.")

# Ловим по callback
async def student_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик ввода или выбора группы"""
    await callbak.message.delete()
    await callbak.answer("")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(FASTAPI_URL + '/groups/') as response:
            groups = await response.json()
    
    if groups:
        await callbak.message.answer("Выберите свою группу", reply_markup=groups)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой группы нет.")

async def teacher_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик выбора предмета"""
    await callbak.message.delete()
    await callbak.answer("")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(FASTAPI_URL + '/disciplines/') as response:
            disciplines = await response.json()
    disciplines = disciplines.get('entities')
    disciplines = set(disciplines)
    if disciplines:
        await callbak.message.answer(f"Выберите свою дисциплину{disciplines}", reply_markup=disciplines)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой дисциплины нет.")

async def register_ending(callbak: CallbackQuery, state: FSMContext):
    """Обработчик завершения регистраций"""
    await callbak.message.delete()
    await state.clear()
    await callbak.message.answer("Вы зарегистрированы.")