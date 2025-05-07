# API для расписания костромского политеха

import asyncio
from typing import Iterable, List, Dict, Any
from datetime import date as Date
from datetime import datetime as DT
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, APIRouter

from core import models
from core.models import DB, Discipline, Lesson, Schedule, Group, Auditory
from core.parser import google
from core.notifications import send_schedule_updates
from core.models import update_schedule


router = APIRouter()

# Глобальный объект для хранения бота
class BotContainer:
    bot = None

def init_bot(bot_instance):
    BotContainer.bot = bot_instance

@router.post("/update_schedule/")
async def api_update_schedule(date: Date, doc_id: str, schedule_data: Dict[str, Any]):
    """API endpoint для обновления расписания с отправкой уведомлений"""
    try:
        changes = await update_schedule(date, doc_id, schedule_data)
        await send_schedule_updates(BotContainer.bot, changes, date)
        return {"status": "success", "changes": changes}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# pylint: disable=E1101
TIME_SHORT_SLEEP = 15 * 60 * 60
TIME_LONG_SLEEP = 15 * 60 * 60 * 60

class CreateUserType(BaseModel):
    chat_id: int
    type: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Перед запуском и завершением работы сервера"""

    async def parsing_schedule():
        """Парсинг с периодичностью"""
        while True:
            await google.run(BotContainer.bot)
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

@app.get('/user/{chat_id}/')
async def get_user_role(chat_id: int):
    """Получение аккаунта пользователя"""
    user = await models.User.aio_get_or_none(chat_id=chat_id)
    student = await models.Student.aio_get_or_none(user_id=user)
    if student:
        return {
            'chat_id': user.chat_id,
            'type': 'student',
            'id': student.group_id
        }

    teacher = await models.Teacher.aio_get_or_none(user_id=user)
    if teacher:
        disciplines = models.Teacher.select().where(models.Teacher.user_id == user.id).prefetch(models.Discipline)
        discipline_list = []
        for teacher_discipline in disciplines:
            discipline_list.append(teacher_discipline.discipline_id.id)

        return {
            'chat_id': user.chat_id,
            'type': 'teacher',
            'id': discipline_list
        }

@app.post('/create/{chat_id}')
async def create_user(chat_id: int):
    """Создание аккаунта пользователя"""
    await models.User.aio_get_or_create(chat_id=chat_id)
    return {'message': 'OK'}

@app.post('/create/teacher/')
async def create_teacher(response: CreateUserType):
    """Создание связи между пользователем и преподавателем"""
    try:
        user, _ = await models.User.aio_get_or_create(chat_id=response.chat_id)
        discipline, _ = await models.Discipline.aio_get_or_create(name=response.type)
        await models.Teacher.aio_get_or_create(user_id=user, discipline_id=discipline)
        return {'message': 'OK'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/create/student/')
async def create_student(response: CreateUserType):
    """Создание связи между пользователем и студентом"""
    try:
        user, _ = await models.User.aio_get_or_create(chat_id=response.chat_id)
        group, _ = await models.Group.aio_get_or_create(name=response.type)
        await models.Student.aio_get_or_create(user_id=user, group_id=group)
        return {'message': 'OK'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put('/updates/group/')
async def update_student(response: CreateUserType):
    """
    Обновить группу студента.

    Args:
        student_id (int): ID студента.
        group_id (int): ID новой группы.

    Raises:
        HTTPException: 404, если студент не найден.
        HTTPException: 404, если группа не найдена.
        HTTPException: 400, если произошла ошибка при обновлении.

    Returns:
        dict: OK.
    """
    try:
        user = await models.User.aio_get_or_none(chat_id=response.chat_id)
        student = await models.Student.aio_get_or_none(user_id = user)
        if not student:
            raise HTTPException(status_code=404, detail="Студент не найден")
        
        group = await models.Group.aio_get_or_none(name=response.type)
        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        student.group_id = group.id
        await student.aio_save()

        return {'message': 'OK'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.delete('/teachet/discipline/{discipline_id}')
async def delete_discipline(discipline_id: int):
    """
    Удалить дисциплину.
    """
    discipline = await models.Teacher.aio_get_or_none(discipline_id=discipline_id)
    if not discipline:
        raise HTTPException(status_code=400, detail=str(e))
    await discipline.aio_delete_instance()
    return {'message': 'OK'}

@app.delete('/teacher/delete/{teacher_id}')
async def delete_teacher(teacher_id: int):
    """Удаление аккаунта преподавателя

    Args:
        teacher_id (int): [teacher -> user]

    Raises:
        HTTPException: [400]

    Returns:
        [message]: [OK(200)]
    """
    user = await models.User.aio_get_or_none(chat_id=teacher_id)
    teacher = await models.Teacher.aio_get_or_none(user_id=user)
    if not teacher:
        raise HTTPException(status_code=404, detail="Связь не найдена")
    while True:
        teacher = await models.Teacher.aio_get_or_none(user_id=user)
        if not teacher:
            break
        await teacher.aio_delete_instance()
    return {'message': 'OK'}

@app.delete('/student/delete/{student_id}')
async def delete_student(student_id: int):
    """Удаление аккаунта студента

    Args:
        student_id (int): [student -> user]

    Raises:
        HTTPException: [400]

    Returns:
        [message]: [OK(200)]
    """
    user = await models.User.aio_get_or_none(chat_id=student_id)
    student = await models.Student.aio_get_or_none(user_id=user)
    if not student:
        raise HTTPException(status_code=404, detail="Связь не найдена")
    await student.aio_delete_instance()
    return {'message': 'OK'}

@app.get('/updates/')
async def get_updates(discipline_id: int = None, group_id: int = None, limit: int = 100):
    """Получить список обновлений занятий"""
    where = models.Schedule.date >= Date.today()
    where &= models.Lesson.arhiv == False
    if discipline_id:
        where &= models.Lesson.discipline_id == discipline_id
    if group_id:
        where &= models.Lesson.group_id == group_id

    lessons: List[models.Lesson] = await DB.aio_execute(
        models.Lesson
        .select(models.Lesson)
        .join(models.Schedule, on=(models.Schedule.id == models.Lesson.schedule_id))
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
    """Получить список расписаний"""
    if date:
        schedules = await DB.aio_execute(
            models.Schedule.filter(date=date)
            .order_by(models.Schedule.date.asc(), models.Schedule.update_at.asc())
        )
    else:
        schedules = await DB.aio_execute(
            models.Schedule.select()
            .order_by(models.Schedule.date.asc(), models.Schedule.update_at.asc())
        )

    return {
        'count': len(schedules),
        'entities': [schedule.to_dict() for schedule in schedules]
    }

async def get_dict_by_schedule(schedule: models.Schedule, group: models.Group = None):
    """Получить полное расписание"""
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")

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
    """Получение расписания по дисциплине"""
    schedule = await models.Schedule.aio_get(id=schedule_id)
    group = await models.Group.aio_get(id=group_id) if group_id else None
    return await get_dict_by_schedule(schedule=schedule, group=group)

@app.get('/schedule/date/{date}/')
async def get_schedule_by_date(date: Date, group_id: int = None):
    """Получение расписания по конкретной дате"""
    schedule = await models.Schedule.aio_get_or_none(date=date)
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание на указанную дату не найдено")

    group = await models.Group.aio_get(id=group_id) if group_id else None
    return await get_dict_by_schedule(schedule=schedule, group=group)

@app.get("/schedule/teacher/{teacher_id}")
async def get_teacher_schedule(teacher_id: int):
    """Получение расписания преподавателя"""
    disciplines = await Discipline.aio_filter(teacher__user_id=teacher_id)
    if not disciplines:
        raise HTTPException(status_code=404, detail="Преподаватель не найден или у него нет дисциплин")

    lessons = await Lesson.aio_filter(discipline__in=[d.id for d in disciplines], arhiv=False)

    response = []
    for lesson in lessons:
        schedule = await Schedule.aio_get(id=lesson.schedule_id)
        group = await Group.aio_get(id=lesson.group_id)
        auditory = await Auditory.aio_get(id=lesson.auditory_id)
        response.append({
            "date": schedule.date,
            "group_name": group.name,
            "pair": lesson.pair,
            "discipline_name": lesson.discipline.name,
            "auditory_name": auditory.name
        })

    return response

@app.get('/date/{id}')
async def get_date_doc(id: int):
    """По айди возвращает дату"""
    date = await models.Schedule.aio_get(id=id)
    if not date:
        raise HTTPException(status_code=404, detail="Дата не найдена")
    return {'date': date.date}

@app.get('/groups/')
async def get_groups():
    """Получить список групп"""
    groups = await DB.aio_execute(models.Group.select())
    return {
        'count': len(groups),
        'entities': [group.to_dict() for group in groups],
    }

@app.get('/group/{group_id}/')
async def get_group_by_id(group_id: int):
    """Получить группу"""
    group = await models.Group.aio_get(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    lessons = await DB.aio_execute(group.lessons.group_by(models.Lesson.schedule))
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
    disciplines = await DB.aio_execute(models.Discipline.select())
    return {
        'count': len(disciplines),
        'entities': [discipline.to_dict() for discipline in disciplines],
    }

@app.get('/discipline/{discipline_id}/')
async def get_discipline_by_id(discipline_id: int):
    """Получить дисциплину"""
    discipline = await models.Discipline.aio_get(id=discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    lessons = await DB.aio_execute(discipline.lessons.group_by(models.Lesson.schedule))
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
    """Получение расписания по дисциплине

    Args:
        schedule_id (int): [номер дисциплины]
        group_id (int, optional): [группа]. Defaults to None.

    Returns:
        [JSON]: [shedule,group]
    """
    schedule = await models.Schedule.aio_get(id=schedule_id)
    group = await models.Group.aio_get(id=group_id) if group_id else None
    return await get_dict_by_schedule(
        schedule=schedule,
        group=group
    )