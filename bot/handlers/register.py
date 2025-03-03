"""Модуль обработки регистраций"""
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.state.state as stat
import bot.keys_board.register as reg
import aiohttp  # Используем aiohttp для асинхронных запросов
from RequestsUrl import service

async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start
    Выбор типа пользователя
    """
    response = await service.get_request(f'/user/role/{message.chat.id}')
    
    if response != 'null':
        await message.answer("Выберите роль", reply_markup=reg.Keyboard_register)
    else:
        await message.answer(
            f"Вы уже зарегистрированы\n {message.from_user.full_name}, выберите роль",
            reply_markup=reg.Keyboard_register
        )
# Ловим по callback
async def student_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик ввода или выбора группы"""
    await callbak.message.answer("Роль успешно присвоена.")
    
    keyboard = await reg.group()
    if keyboard:
        await callbak.message.answer("Выберите свою группу, для получения рассписания", reply_markup=keyboard)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой группы нет.")

async def teacher_register(callbak: CallbackQuery, state: FSMContext):
    """Обработчик выбора предмета"""
    await callbak.message.answer("Роль успешно присвоена.")
    disciplines = service.get_request('/disciplines/')
    disciplines = disciplines.get('entities')
    disciplines = set(disciplines)
    if disciplines:
        await callbak.message.answer(f"Выберите свою дисциплину{disciplines}", reply_markup=disciplines)
        await state.set_state(stat.User.reg_end)
    else:
        await callbak.message.answer("На данный момент такой дисциплины нет.")

async def register_ending(callbak: CallbackQuery, state: FSMContext):
    """Обработчик завершения регистраций"""
    response = callbak.data.split('_')
    if response[0] == 'discipline':
        await service.post_request(f'/create/',json={
            'user_id': str(callbak.message.chat.id),
            'category_type': 'disciplines',
            'category_name': response[1]
        })
    else:
        await service.post_request(f'/create/',json={
            'user_id': str(callbak.message.chat.id),
            'category_type': 'group',
            'category_name': response[1]
        })
    await callbak.message.delete()
    await state.clear()
    await callbak.message.answer("Вы зарегистрированы.")