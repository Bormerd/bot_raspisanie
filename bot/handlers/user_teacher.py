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
    ]
    await bot.set_my_commands(commands)

async def sending_update(message: Message):
    """Отправляет обновления расписания преподавателю по его дисциплинам.
    Проверяет наличие новой или измененной информации о расписании и отправляет
    соответствующие обновления преподавателю.

    Args:
        message (Message): Объект сообщения, который запустил эту функцию.
    """
    # Предположим, что ID преподавателя передается в сообщении
    service.post_request("/check-updates/")
    data = await response.json()
    if data.get("message") == "Изменения обнаружены.":
        teacher_id = message.from_user.id  # ID пользователя в Telegram

        # Получаем дисциплины преподавателя
        teacher_response = await service.get_request(f'/user/{teacher_id}/')
        teacher_disciplines = teacher_response.get('disciplines', [])  # Предполагаем, что ключ 'disciplines' содержит список дисциплин
        discipline_ids = [d['id'] for d in teacher_disciplines]  # Извлекаем ID дисциплин

        if not discipline_ids:
            await message.answer("У вас нет назначенных дисциплин.")
            return

        # Получаем расписание для дисциплин преподавателя
        schedules = []
        for discipline_id in discipline_ids:
            schedules_response = await service.get_request(f'/updates/?discipline_id={discipline_id}')
            schedule = schedules_response.get("entities", [])
            schedules.extend(schedule)  # Используем extend для добавления элементов списка

        # Группируем занятия по дате
        lessons_by_date = defaultdict(list)
        for schedule in schedules:
            schedule_id = schedule.get("id")

            # Получаем детали расписания
            schedule_details_response = await service.get_request(f'/schedule/{schedule_id}/')
            schedule_details = schedule_details_response.get("entities", [])

            for lesson in schedule_details:
                lesson_date = lesson.get("date")
                lessons_by_date[lesson_date].append(lesson)

        # Формируем сообщение с изменениями
        update_message = format_teacher_update_message(lessons_by_date)

        # Отправляем сообщение преподавателю
        if update_message:
            await message.answer(update_message)
        else:
            await message.answer("Нет новых изменений в расписании.")
    await asyncio.sleep(
                TIME_LONG_SLEEP
                if now.hour >= 8 and now.hour < 17
                else TIME_LONG_SLEEP
            )

def format_teacher_update_message(lessons_by_date: defaultdict) -> str:
    """Форматирует сообщение с обновлениями для преподавателя."""
    if not lessons_by_date:
        return ""

    message = "Обновления расписания:\n"
    for date, lessons in sorted(lessons_by_date.items()):
        message += f"\n📅 Дата: {date}\n"
        for lesson in lessons:
            if lesson.get('old_lesson') is None:
                message += f"✅ Добавлено новое занятие: {lesson['title']} (Группа: {lesson['group_id']})\n"
            else:
                message += f"🔄 Изменено занятие: {lesson['title']} (Группа: {lesson['group_id']})\n"
    return message

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

        # Формируем и отправляем сообщения
        for date, lessons in lessons_by_date.items():
            # Сортируем занятия по номеру пары
            lessons_sorted = sorted(lessons, key=lambda x: x.get("pair"))

            # Формируем сообщение
            message_text = f"📅 <b>{date}:</b>\n\n"
    
    # Если расписание пустое, сообщаем об этом
            if not lessons_sorted:
                message_text += "🎉 <i>На этот день занятий нет!</i>"
            else:
                # Проходим по каждому уроку и добавляем информацию в сообщение
                for lesson in lessons_sorted:
                    discipline = lesson.get("discipline", {}).get("name", "Неизвестно")
                    auditory = lesson.get("auditory", {}).get("name", "Неизвестно")
                    pair = lesson.get("pair", "Неизвестно")
                    group = lesson.get("group", {}).get("name", "Неизвестно")

                    # Форматируем информацию о паре
                    message_text += (
                        f"{pair}️⃣ 📖 <b>{discipline}</b> | 🚪 <b>{auditory}</b>\n"
                    )
            # Добавляем перерыв, если это необходимо (например, после второй пары)

            # Отправляем сообщение с HTML-форматированием
            await message.answer(message_text, parse_mode="HTML")

async def add_disciplines (message: Message, state: FSMContext):
    """Функция добавления дисциплин преподавателю."""
    keyboard = await tea.discipline()
    if keyboard:
        await message.answer(f"Выберите свою дисциплину", reply_markup=keyboard)
        await state.set_state(stat.User.add_discipline)
    else:
        await message.answer("На данный момент такой дисциплины нет.")

async def add_discipline_user(callbak: CallbackQuery):
    await callbak.message.delete()
    response = callbak.data.split('_')
    if response[0] == 'disciplines':
        await service.post_request('/create/teacher/', json={
            'chat_id': callbak.message.chat.id,
            'type': response[1]
        })
    await callbak.message.answer("Дисциплина добавлена")

async def delete_discipline(message: Message, state: FSMContext):
    """Функция удаления дисциплин преподавателю."""
    chat_id = message.from_user.id
    keyboard,count = await tea.user_discipline(chat_id)
    if count != 1:
        await message.answer("Выберите дисциплину:", reply_markup=keyboard)
        await state.set_state(stat.User.delete_discipline)
    else:
        await message.answer("У вас только 1 дисциплина.")

async def delete_discipline_user(callbak:CallbackQuery):
    await callbak.message.delete()
    response = callbak.data.split('_')
    await service.delete_request(f'/teachet/discipline/{response[1]}')
    await callbak.message.answer("Дисциплина удалена")
    