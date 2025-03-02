#API для расписания костромского политеха 

import asyncio
from typing import Iterable, List
from datetime import date as Date
from datetime import datetime as DT
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, Optional
from fastapi import FastAPI

from core import models
from core.models import DB
from core.parser import google


# pylint: disable=E1101
TIME_SHORT_SLEEP = 15 * 60 * 60
TIME_LONG_SLEEP = 15 * 60 * 60 * 60

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Перед запуском и завершением работы сервера"""

    async def parsing_schedule():
        """Парсинг с периодичностью"""
        while True:
            await google.run()
            now = DT.now().time()
            await asyncio.sleep(
                TIME_SHORT_SLEEP
                if now.hour >= 8 and now.hour < 17
                else TIME_LONG_SLEEP
            )
    task = parsing_schedule()
    asyncio.create_task(task)

    yield
    task.close()
    if not DB.is_closed():
        DB.close()


app = FastAPI(lifespan=lifespan)

@app.get('/user/role/{user_id}')
async def get_user_role(user_id: str):
    user = await models.UserDisciplines.aio_get_or_none(user_id=user_id)
    if user:
        return {'message': 'OK'}

@app.post('/create/')
async def create_user(
    user_id: str,
    category_type: str,
    category_name: Optional[str]
) -> dict:
    """
    Создать пользователя и вернуть информацию о нём.

    :param user_id: Идентификатор пользователя.
    :param category_type: Тип категории ('group' или 'discipline').
    :param category_name: Название группы или дисциплины (опционально).
    :return: Словарь с информацией о созданном пользователе.
    """

    # Создаём пользователя
    user = await DB.aio_execute(
        models.Users,
        user_id=user_id,
        category_type=category_type,
        category_name=category_name
    )


@app.get('/updates/')
async def get_updates(

        discipline_id: int = None,
        group_id: int = None,
        limit: int = 100):
    """Получить список обновлений занятий.
    Если old_lesson = null значит предыдущего занятия не было,
    то есть занятие добавилось, а не изменилось"""

    where = models.Schedule.date >= Date.today()
    where &= models.Lesson.arhiv == False
    if discipline_id:
        where &= models.Lesson.discipline_id == discipline_id
    if group_id:
        where &= models.Lesson.group_id == group_id

    lessons: List[models.Lesson] = await DB.aio_execute(
        models.Lesson
        .select(models.Lesson)
        .join(
            models.Schedule,
            on=(models.Schedule.id == models.Lesson.schedule_id)
        )
        .where(where)
        .order_by(models.Lesson.id.desc())
        .limit(limit)
    )
    return {
        'count': len(lessons),
        'entities': [lesson.to_dict() for lesson in lessons]
    }


@app.get('/schedules/')
async def get_schedules(date: Date = None):
    """Получить список расписаний. Если date - не указан,
 то верент расписание от текущей даты и позже"""
    if date:
        schedules = await DB.aio_execute(
            models.Schedule
            .filter(
                date=date
            )
            .order_by(
                models.Schedule.date.asc(),
                models.Schedule.update_at.asc(),
            )
        )
    else:
        schedules = await DB.aio_execute(
            models.Schedule.select().where(
                models.Schedule.date >= Date.today()
            )
            .order_by(
                models.Schedule.date.asc(),
                models.Schedule.update_at.asc(),
            )
        )

    return {
        'count': len(schedules),
        'entities': [schedule.to_dict() for schedule in schedules]
    }


async def get_dict_by_schedule(
        schedule: models.Schedule,
        group: models.Group = None):
    """Получить полное расписание"""

    lessons: Iterable[models.Lesson] = await DB.aio_execute(schedule.lessons)

    result = {
        'count': 0,
        'entities': [],
    }

    for lesson in lessons:
        if group and lesson.group != group:
            continue

        row = {
            'group': lesson.group.to_dict(),
            'pair': lesson.pair,
            'discipline': lesson.discipline.to_dict(),
            'auditory': lesson.auditory.to_dict(),
        }
        result['entities'].append(row)

    result['count'] = len(result['entities'])
    return result


@app.get('/schedule/{schedule_id}/')
async def get_schedule(schedule_id: int, group_id: int = None):
    """Получить расписание"""
    schedule = await models.Schedule.aio_get(id=schedule_id)
    group = await models.Group.aio_get(id=group_id) if group_id else None
    return await get_dict_by_schedule(
        schedule=schedule,
        group=group
    )


@app.get('/groups/')
async def get_groups():
    """Получить список групп"""

    groups = await DB.aio_execute(
        models.Group.select()
    )

    return {
        'count': len(groups),
        'entities': [group.to_dict() for group in groups],
    }


@app.get('/group/{group_id}/')
async def get_group_by_id(group_id: int):
    """Получить группу"""

    group = await models.Group.aio_get(id=group_id)
    lessons = await DB.aio_execute(
        group.lessons.group_by(models.Lesson.schedule)
    )
    return {
        **group.to_dict(),
        'schedules': {
            'count': len(lessons),
            'entities': [
                lesson.schedule.to_dict() for lesson in lessons
                if lesson.schedule.date >= Date.today()
            ]
        },
    }


@app.get('/disciplines/')
async def get_discipline():
    """Получить список дисциплин"""
    disciplines = await DB.aio_execute(
        models.Discipline.select()
    )

    return {
        'count': len(disciplines),
        'entities': [discipline.to_dict() for discipline in disciplines],
    }


@app.get('/discipline/{discipline_id}/')
async def get_discipline_by_id(
        discipline_id: int):
    """Получить группу"""

    discipline = await models.Discipline.aio_get(id=discipline_id)
    lessons = await DB.aio_execute(
        discipline.lessons.group_by(models.Lesson.schedule)
    )
    return {
        **discipline.to_dict(),
        'schedules': {
            'count': len(lessons),
            'entities': [
                lesson.schedule.to_dict() for lesson in lessons
                if lesson.schedule.date >= Date.today()
            ]
        },
    }
