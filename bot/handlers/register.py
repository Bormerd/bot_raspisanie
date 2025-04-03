"""Модуль обработки регистраций"""
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.state.state as stat
import bot.keys_board.register as reg
import aiohttp
from api.RequestsUrl import service
from aiohttp import ClientResponseError

async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start
    Выбор типа пользователя
    """
    response = await service.get_request(f'/user/{message.chat.id}/')
    
    if response == 'null':
        await service.post_request(f'/create/{message.chat.id}/')
        await message.answer("Выберите роль", reply_markup=reg.Keyboard_register)
    else:
        await message.answer("Изменить роль", reply_markup=reg.Keyboard_register)

async def student_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик ввода или выбора группы"""   
    await callbak.message.delete()
    keyboard = await reg.group()
    if keyboard:
        response = await service.get_request(f'/user/{callbak.message.chat.id}/')
        if response and response['type'] == 'teacher':
            await service.delete_request(f'/teacher/delete/{callbak.message.chat.id}')
        await callbak.message.answer("Выберите свою группу, для получения рассписания", reply_markup=keyboard)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой группы нет.")

async def teacher_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик выбора предмета"""
    await callbak.message.delete()
    keyboard = await reg.discipline()
    if keyboard:
        response = await service.get_request(f'/user/{callbak.message.chat.id}/')
        if response and response['type'] == 'student':
            await service.delete_request(f'/student/delete/{callbak.message.chat.id}')
        await callbak.message.answer(f"Выберите свою дисциплину", reply_markup=keyboard)
        await state.set_state(stat.User.reg_end)

    else:
        await callbak.message.answer("На данный момент такой дисциплины нет.")

async def register_ending(callbak: CallbackQuery, state: FSMContext):
    """Обработчик завершения регистраций"""
    response = callbak.data.split('_')
    user = await service.get_request(f'/user/{callbak.message.chat.id}/')
    if user and user['type'] == 'student':
        await service.put_request(f'/updates/group/',json={
            'chat_id': callbak.message.chat.id, 
            'type': response[1]
        })
    elif response[0] == 'disciplines':
        await service.post_request('/create/teacher/', json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
            })
    else:
        await service.post_request('/create/student/',json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
        })
        await callbak.message.answer(f"Группа изменина на {response[1]}")
    await callbak.message.delete()
    await state.clear()
    await callbak.message.answer("Вы зарегистрированы.")