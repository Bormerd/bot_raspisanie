"""Модуль обработки регистраций"""
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.state.state as stat
import bot.keys_board.register as reg
import aiohttp  # Используем aiohttp для асинхронных запросов
from RequestsUrl import service
from aiohttp import ClientResponseError

async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start
    Выбор типа пользователя
    """
    response = await service.get_request(f'/user/{message.chat.id}/')
    
    if response != 'null':
        await service.post_request(f'/create/{message.chat.id}/')
        await message.answer("Выберите роль", reply_markup=reg.Keyboard_register)
    else:
        await message.answer("Вы уже зарегистрированы")

async def student_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик ввода или выбора группы"""   
    keyboard = await reg.group()
    if keyboard:
        await callbak.message.answer("Выберите свою группу, для получения рассписания", reply_markup=keyboard)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой группы нет.")

async def teacher_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик выбора предмета"""
    keyboard = await reg.discipline()
    if keyboard:
        await callbak.message.answer(f"Выберите свою дисциплину", reply_markup=keyboard)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой дисциплины нет.")

async def register_ending(callbak: CallbackQuery, state: FSMContext):
    """Обработчик завершения регистраций"""
    response = callbak.data.split('_')
    if response[0] == 'disciplines':
        await service.post_request('/create/teacher/', json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
        })
    else:
        await service.post_request('/create/student/',json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
        })
    await callbak.message.delete()
    await state.clear()
    await callbak.message.answer("Вы зарегистрированы.")