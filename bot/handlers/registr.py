"""Модуль обработки регистраций"""
# может не хватать библеотек
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
import bot.stater.state as stat
import bot.keys_board.register as reg

async def command_start_handler(message: Message,state :FSMContext) -> None:
    """"
    Обработчик команды /start
    Выбор типа пользователя
    """
    user=bool(User.get_or_none(User.chat_id == message.from_user.id) is None)
    if user:
        await message.answer("Выбирите")
        await state.set_state(stat.User.role)
    else:
        user=User.get(User.chat_id == message.from_user.id)
        await message.answer(
            f"Вы уже зарегистрированы\n {user.user_name}, Выберите роль",
            reply_markup=reg.Keyboard_register
            )

async def student_register(callbak :CallbackQuery,state: FSMContext):
    """Обработчик ввода или выбора группы"""
    await callbak.message.delete()
    await callbak.answer("")
    # отправка запроса в FastApi JSON от туда из бд (пользователь -> группа)
    if groups:
        await callbak.message.answer("Выберите свою группу",reply_markup=groups)
        await state.set_state(stat.user.reg_end)
    else:
        await callbak.message.answer("На данный момент такой групп нет")

async def teacher_register(callbak :CallbackQuery,state: FSMContext):
    """Обработчик выбора предмета"""
    await callbak.message.delete()
    await callbak.answer("")
    # отправка запроса в FastApi JSON от туда из бд (пользователь -> предмет)
    if discipline:
        await callbak.message.answer("Выберите свою дисциплину",reply_markup=discipline)
        await state.set_state(stat.user.reg_end)
    else:
        await callbak.message.answer("На данный момент такой дисциплины нет")


async def register_ending(callbak:CallbackQuery,state: FSMContext):
    """Обработчик завершения регестраций"""
    await callbak.message.delete()
    # Перепесать отправку данных в FastApi JSON от туда в бд
    # user=User.get(User.chat_id == callbak.message.chat.id)
    # group=Group.get(Group.group_name == callbak.data.split('_')[1])
    # Student.get_or_create(user=user,group=group)
    await state.clear()
    await callbak.message.answer("Вы зарегестрированы.")



