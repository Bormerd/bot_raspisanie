"""Модуль обработки команд Преподователя"""
# может не хватать библеотек
from peewee import IntegrityError
from aiogram import Bot
from aiogram.types import Message,CallbackQuery,BotCommand
from aiogram.fsm.context import FSMContext
import bot.keys_board.teacher as tea
import bot.state.state as stat
from RequestsUrl import service
from collections import defaultdict

async def menu_teacher(message:Message,state:FSMContext,bot: Bot) -> None:
    """""
    Функция для вывода меню
    """
    await state.clear()
    await message.answer("Меню возможностей",reply_markup=tea.Teacher_menu)
    from main import bot
    commands = [
        BotCommand(command="/add_discipline", description="добавить дисциплину"),
        BotCommand(command="/delete_discipline", description="удалить дисциплину"),
        BotCommand(command="/schedule",description="Расписанеи"),
        BotCommand(command="/menu", description="Меню")
    ]
    await bot.set_my_commands(commands)

async def discipline_schedule (message: Message):
    """Отправка расписания"""
    # написать запрос для вывода расписания ОДНОЙ дисциплины
    pass

async def teacher_schedule(message: Message):
    """Отправка расписания для преподавателя"""
    teacher_id = message.chat.id

    # Получаем список всех расписаний
    schedules_response = await service.get_request('/schedules/')
    schedules = schedules_response.get("entities", [])

    if not schedules:
        await message.answer("Нет доступных расписаний.")
        return

    # Получаем дисциплины преподавателя
    teacher_response = await service.get_request(f'/user/{teacher_id}/')
    teacher_disciplines = teacher_response.get('id', [])
    discipline_ids = teacher_disciplines 
    if not discipline_ids:
        await message.answer("У вас нет назначенных дисциплин.")
        return

    for schedule in schedules:
        schedule_id = schedule.get("id")

        # Получаем детали расписания
        schedule_details_response = await service.get_request(f'/schedule/{schedule_id}/')
        schedule_details = schedule_details_response.get("entities", [])
        lessons_by_date = defaultdict(list)

        # Фильтруем занятия по дисциплинам преподавателя
        for detail in schedule_details:
            if detail.get("discipline", {}).get("id") in discipline_ids:
                lessons_by_date[schedule['date']].append(detail)

        # if lessons_by_date:
        #     await message.answer("У вас нет занятий в текущем расписании.")
        #     return

        # Формируем и отправляем сообщения
        for date, lessons in lessons_by_date.items():
            # Сортируем занятия по номеру пары
            lessons_sorted = sorted(lessons, key=lambda x: x.get("pair"))

            # Формируем сообщение
            message_text = f"<b>Расписание на {date}:</b>\n"
            for lesson in lessons_sorted:
                discipline = lesson.get("discipline", {}).get("name", "Неизвестно")
                auditory = lesson.get("auditory", {}).get("name", "Неизвестно")
                pair = lesson.get("pair")
                group = lesson.get("group", {}).get("name", "Неизвестно")
                message_text += f"<b>{pair}) {discipline} ({auditory})</b> для группы <b>{group}</b>\n"

            # Отправляем сообщение
            await message.answer(message_text, parse_mode="HTML")

async def add_disciplines (message: Message, state: FSMContext):
    keyboard = await tea.discipline()
    if keyboard:
        await message.answer(f"Выберите свою дисциплину", reply_markup=keyboard)
        await state.set_state(stat.User.add_discipline)
    else:
        await message.answer("На данный момент такой дисциплины нет.")

async def add_discipline_user(callbak: CallbackQuery):
    response = callbak.data.split('_')
    if response[0] == 'disciplines':
        await service.post_request('/create/teacher/', json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
        })
    await callbak.message.answer("Дисциплина добавлена")
