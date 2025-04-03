"""API"""
import asyncio
from typing import Iterable, List
from datetime import date as Date
from datetime import datetime as DT
from contextlib import asynccontextmanager
from pydantic import BaseModel
from collections import defaultdict
from fastapi import FastAPI, HTTPException
from core import models
from core.models import DB
from core.parser import google
from bot.handlers.bot_notifier import BotNotifier
from core.service import get_request
import redis
import json

class ScheduleNotifier:
    @staticmethod
    async def get_user_info(chat_id: int) -> dict:
        """Получаем информацию о пользователе"""
        user = await models.User.aio_get_or_none(chat_id=chat_id)
        if not user:
            return None

        student = await models.Student.aio_get_or_none(user_id=user)
        if student:
            return {
                'chat_id': chat_id,
                'type': 'student',
                'id': student.group_id
            }

        teacher = await models.Teacher.aio_get_or_none(user_id=user)
        if teacher:
            disciplines = await models.Teacher.aio_filter(user_id=user)
            discipline_list = [t.discipline_id.id for t in disciplines]
            return {
                'chat_id': chat_id,
                'type': 'teacher',
                'id': discipline_list
            }

        return None

    @staticmethod
    async def format_teacher_schedule(
        schedule_data: List[dict], schedule_date: Date
    ) -> str:
        """Форматируем расписание для преподавателя в едином стиле"""
        message_text = (
            f"🔔 Обнаружено новое/измененное расписание на {schedule_date}\n\n"
            f"📅 <b>{schedule_date}:</b>\n\n"
        )

        lessons_by_pair = defaultdict(list)
        for lesson in schedule_data:
            lessons_by_pair[lesson['pair']].append(lesson)

        for pair in sorted(lessons_by_pair.keys()):
            lessons = lessons_by_pair[pair]
            lessons = lessons[0]['discipline_name']
            message_text += f"{pair}️⃣ 📖 <b>{lessons}</b>\n"

            for lesson in lessons:
                message_text += (
                    f"   👥 Группа: {lesson['group_name']}\n"
                    f"   🚪 Ауд.: {lesson['auditory_name']}\n"
                )

            message_text += "\n"

        if not lessons_by_pair:
            message_text += "🎉 <i>На этот день занятий нет!</i>"

        return message_text

    @staticmethod
    async def format_student_schedule(
        schedule_data: List[dict],
        schedule_date: Date
    ) -> str:
        """Форматируем расписание для студента в едином стиле"""
        message_text = (
            f"🔔 Обнаружено новое/измененное расписание на {schedule_date}\n\n"
            f"📅 <b>{schedule_date}:</b>\n\n"
        )

        sorted_lessons = sorted(schedule_data, key=lambda x: x['pair'])

        for lesson in sorted_lessons:
            message_text += (
                f"{lesson['pair']}️⃣ 📖 <b>{lesson['discipline_name']}</b>\n"
                f"   🚪 Ауд.: {lesson['auditory_name']}\n\n"
            )

        if not sorted_lessons:
            message_text += "🎉 <i>На этот день занятий нет!</i>"

        return message_text

    @staticmethod
    async def get_full_day_schedule(
        schedule_date: Date,
        user_info: dict
    ) -> str:
        """Получаем полное расписание на день для пользователя"""
        if user_info['type'] == 'student':
            # Для студента - расписание его группы
            schedule_response = await get_request(
                f'/schedule/date/{schedule_date}/?group_id={user_info["id"]}'
            )

            if not schedule_response or not schedule_response.get('entities'):
                return None

            schedule_data = [{
                'pair': lesson['pair'],
                'discipline_name': lesson['discipline']['name'],
                'auditory_name': lesson['auditory']['name']
            } for lesson in schedule_response['entities']]

            return await ScheduleNotifier.format_student_schedule(
                schedule_data,
                schedule_date
            )

        else:
            # Для преподавателя - расписание по его дисциплинам
            schedule_response = await get_request(
                f'/schedule/teacher/{user_info["chat_id"]}/'
            )

            if not schedule_response:
                return None

            # Фильтруем по дате и преобразуем данные
            schedule_data = []
            for item in schedule_response:
                if item['date'] == str(schedule_date):
                    schedule_data.append({
                        'pair': item['pair'],
                        'discipline_name': item['discipline_name'],
                        'group_name': item['group_name'],
                        'auditory_name': item['auditory_name']
                    })

            return await ScheduleNotifier.format_teacher_schedule(
                schedule_data,
                schedule_date
            )

    @staticmethod
    async def send_schedule_update(chat_id: int, schedule_date: Date):
        """Отправляем обновленное расписание пользователю"""
        user_info = await ScheduleNotifier.get_user_info(chat_id)
        if not user_info:
            return

        schedule_text = await ScheduleNotifier.get_full_day_schedule(
            schedule_date,
            user_info
        )
        if not schedule_text:
            schedule_text = (
                f"🔔 Обнаружено изменение расписания на {schedule_date}\n\n"
                "🎉 На этот день занятий нет!"
            )

        await BotNotifier.send_message(chat_id, schedule_text)


async def check_schedule_changes(last_check_time):
    """Проверяем изменения в расписании"""
    print(f"Ищем изменения после {last_check_time}")

    changed_schedules = await models.Schedule.aio_filter(
        update_at__gte=last_check_time
    ).prefetch(
        models.Lesson,
        models.Lesson.group,
        models.Lesson.discipline,
        models.Lesson.auditory
    )

    print(f"Найдено измененных расписаний: {len(changed_schedules)}")

    affected_users = set()
    for schedule in changed_schedules:
        print(f"Обрабатываем расписание на "
              f"{schedule.date} (ID: {schedule.id})")

        for lesson in schedule.lessons:
            # Студенты группы
            students = await models.Student.aio_filter(
                group_id=lesson.group_id
                )
            for student in students:
                user = await student.user_id
                affected_users.add((user.chat_id, schedule.date))
                print(f"Добавлен студент {user.chat_id}")

            # Преподаватели дисциплины
            teachers = await models.Teacher.aio_filter(
                discipline_id=lesson.discipline_id
                )
            for teacher in teachers:
                user = await teacher.user_id
                affected_users.add((user.chat_id, schedule.date))
                print(f"Добавлен преподаватель {user.chat_id}")

    print(f"Всего пользователей для уведомления: {len(affected_users)}")
    return affected_users


async def parsing_schedule():
    """Парсинг с периодичностью и отправкой уведомлений"""
    last_parsed_time = None

    while True:
        try:
            await google.run()
            if last_parsed_time is not None:
                affected_users = await check_schedule_changes(last_parsed_time)
                for chat_id, schedule_date in affected_users:
                    try:
                        await ScheduleNotifier.send_schedule_update(
                            chat_id,
                            schedule_date
                            )
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"Ошибка при отправке "
                              f"уведомления {chat_id}: {e}")

            last_parsed_time = DT.now()
        except Exception as e:
            print(f"Критическая ошибка в parsing_schedule: {e}")

        now = DT.now().time()
        sleep_time = TIME_SHORT_SLEEP if 8 <= now.hour < 17 else TIME_LONG_SLEEP
        await asyncio.sleep(sleep_time)

# pylint: disable=E1101
TIME_SHORT_SLEEP = 15 * 60 * 60
TIME_LONG_SLEEP = 15 * 60 * 60 * 60

redis_client = redis.Redis(host='localhost', port=6379, db=0)


class CreateUserType(BaseModel):
    chat_id: int
    type: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Перед запуском и завершением работы сервера"""
    task = asyncio.create_task(parsing_schedule())

    def handle_exception(loop, context):
        print(f"Исключение в event loop: {context}")

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Задача проверки расписания корректно завершена")

    if not DB.is_closed():
        DB.close()

app = FastAPI(lifespan=lifespan)

@app.get('/user/{chat_id}/')
async def get_user_role(chat_id: int):
    """Получение аккаунта пользователя"""
    cached_data = redis_client.get(f'user:{chat_id}')
    if cached_data:
        return json.loads(cached_data)
    
    user = await models.User.aio_get_or_none(chat_id=chat_id)
    if not user:
        return None
    
    result = None

    student = await models.Student.aio_get_or_none(user_id=user)
    if student:
        result = {
            'chat_id': user.chat_id,
            'type': 'student',
            'id': student.group_id
        }
    else:
        teacher = await models.Teacher.aio_get_or_none(user_id=user)
        if teacher:
            disciplines = await models.Teacher.filter(
                user_id=user.id
            ).prefetch_related('discipline')
            discipline_list = [d.discipline.id for d in disciplines]
            result = {
                'chat_id': user.chat_id,
                'type': 'teacher',
                'id': discipline_list
            }
    if result:
        redis_client.setex(
            f'user:{chat_id}',
            3600,
            json.dumps(result, default = str)
        )
    
    return result


@app.post('/create/{chat_id}')
async def create_user(chat_id: int):
    """Создание аккаунта пользователя

    Args:
        chat_id (int): [Chat id user]

    Returns:
        [message]: [OK (200)]
    """

    # Создаём пользователя

    await models.User.aio_get_or_create(
        chat_id=chat_id,
    )
    return {'message': 'OK'}


@app.post('/create/teacher/')
async def create_teacher(response: CreateUserType):
    """Создание связи между пользователем и преподавателем"""
    try:
        user, created = await models.User.aio_get_or_create(chat_id=response.chat_id)
        discipline, _ = await models.Discipline.aio_get_or_create(
            name=response.type
        )
        await models.Teacher.aio_get_or_create(
            user_id=user,
            discipline_id=discipline
        )
        if not created:
            disciplines = await models.Teacher.filter(
                user_id=user.id
            ).prefetch_related('discipline')
            
            redis_client.setex(
                f'user:{response.chat_id}',
                3600,
                json.dumps({
                    'chat_id': user.chat_id,
                    'type': 'teacher',
                    'id': [d.discipline.id for d in disciplines],
                },default = str, ensure_ascii=False)
            )
        return {'message': 'OK', 'created': created}
    
    except Exception as e:
        await models.Teacher.filter(
            user_id=user.id,
            discipline_id=discipline.id
        ).adelete()
        raise HTTPException(status_code=400, detail=str(e))



@app.post('/create/student/')
async def create_student(response: CreateUserType):
    """Создание связи между пользователем и студентом"""
    try:
        user, user_created = await models.User.aio_get_or_create(chat_id=response.chat_id)
        group, group_created = await models.Group.aio_get_or_create(name=response.type)
        student, student_created = await models.Student.aio_get_or_create(
            user_id=user,
            group_id=group
        )
        if redis_client:
            redis_client.delete(f"user:{response.chat_id}")
            redis_client.delete(f"group:{group.id}")
            student_data = {
                'user_id': user.id,
                'chat_id': user.chat_id,
                'group_id': group.id,
                'group_name': group.name,
                'created_at': datetime.now().isoformat()
            }
            redis_client.setex(
                f"student:{user.id}",
                3600,
                json.dumps(student_data, default=str)
            )
        
        return {
            'message': 'OK',
            'created': {
                'user': user_created,
                'group': group_created,
                'student': student_created
            }
        }
        
    except Exception as e:
        if 'user' in locals() and 'group' in locals():
            await models.Student.filter(
                user_id=user,
                group_id=group
            ).adelete()
            if 'user_created' in locals() and user_created:
                await user.adelete()
            if 'group_created' in locals() and group_created:
                await group.adelete()
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при создании студента: {str(e)}"
        )


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
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )
        student = await models.Student.aio_get_or_none(user_id=user)
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Студент не найден"
            )
        group, created = await models.Group.aio_get_or_create(
            name=response.type
        )

        student.group_id = group.id
        await student.aio_save()
        if redis_client:
            redis_client.delete(f"user:{response.chat_id}")
            redis_client.delete(f"student:{user.id}")
            redis_client.delete(f"group:{group.id}")
            student_data = {
                'user_id': user.id,
                'chat_id': user.chat_id,
                'group_id': group.id,
                'group_name': group.name,
                'updated_at': datetime.now().isoformat()
            }
            redis_client.setex(
                f"student:{user.id}",
                3600,
                json.dumps(student_data, default=str)
            )

        return {
            'message': 'OK',
            'group_created': created,
            'new_group_id': group.id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error updating student group: {str(e)}")
        
        raise HTTPException(
            status_code=400,
            detail="Ошибка при обновлении группы студента"
        )


@app.delete('/teachet/discipline/{discipline_id}')
async def delete_discipline(discipline_id: int):
    """
    Удалить дисциплину.
    """
    try:
        teacher_discipline = await models.Teacher.aio_get_or_none(
            discipline_id=discipline_id
        )
        if not teacher_discipline:
            raise HTTPException(
                status_code=404,
                detail="Связь преподавателя с дисциплиной не найдена"
            )
        teacher_id = teacher_discipline.user_id
        await teacher_discipline.aio_delete_instance()
        if redis_client:
            redis_client.delete(f"teacher:{teacher_id}")
            redis_client.delete(f"discipline:{discipline_id}")
            redis_client.delete("teachers_disciplines_list")

        return {
            'message': 'OK',
            'deleted': True,
            'teacher_id': teacher_id,
            'discipline_id': discipline_id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка удаления дисциплины: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Ошибка при удалении связи преподавателя с дисциплиной"
        )

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
    try:
        user = await models.User.aio_get_or_none(chat_id=teacher_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )

        teacher_exists = await models.Teacher.aio_exists(user_id=user)
        if not teacher_exists:
            raise HTTPException(
                status_code=404,
                detail="У преподавателя нет связанных дисциплин"
            )

        deleted_count = 0
        while True:
            teacher = await models.Teacher.aio_get_or_none(user_id=user)
            if not teacher:
                break
                
            discipline_id = teacher.discipline_id.id if teacher.discipline_id else None
        
            await teacher.aio_delete_instance()
            deleted_count += 1
            if redis_client and discipline_id:
                redis_client.delete(f"discipline:{discipline_id}")
        if redis_client:
            redis_client.delete(f"teacher:{user.id}")
            redis_client.delete(f"user:{teacher_id}")
            redis_client.delete("teachers_list")

        return {
            'message': 'OK',
            'deleted_count': deleted_count,
            'teacher_id': user.id,
            'chat_id': teacher_id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка удаления дисциплин преподавателя: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Ошибка при удалении связей преподавателя"
        )

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
    try:
        user = await models.User.aio_get_or_none(chat_id=student_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )

        student = await models.Student.aio_get_or_none(user_id=user)
        if not student:
            raise HTTPException(
                status_code=404,
                detail="Студент не найден"
            )

        user_id = user.id
        group_id = student.group_id.id if student.group_id else None

        await student.aio_delete_instance()

        if redis_client:
            redis_client.delete(f"user:{student_id}")
            redis_client.delete(f"student:{user_id}")
            if group_id:
                redis_client.delete(f"group:{group_id}")
            redis_client.delete("students_list")

        return {
            'message': 'OK',
            'deleted': True,
            'user_id': user_id,
            'chat_id': student_id,
            'group_id': group_id
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка удаления студента: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Ошибка при удалении студента"
        )


@app.get('/updates/')
async def get_updates(
    discipline_id: int = None,
    group_id: int = None,
    limit: int = 100
):
    """Получить список обновлений занятий"""
    cache_key = f"updates:{discipline_id}:{group_id}:{limit}"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    where = models.Schedule.date >= Date.today()
    where &= models.Lesson.arhiv == False
    if discipline_id:
        where &= models.Lesson.discipline_id == discipline_id
    if group_id:
        where &= models.Lesson.group_id == group_id

    lessons: List[models.Lesson] = await DB.aio_execute(
        models.Lesson
        .select(models.Lesson)
        .join(models.Schedule, on=(
            models.Schedule.id == models.Lesson.schedule_id
            ))
        .where(where)
        .order_by(models.Lesson.id.desc())
        .limit(limit)
    )

    result = {
        'count': len(lessons),
        'entities': [lesson.to_dict() for lesson in lessons]
    }

    if redis_client:
        redis_client.setex(
            cache_key,
            1800,
            json.dumps(result, default=str)
        )
    
    return result


@app.get('/schedules/')
async def get_schedules(date: Date = None):
    """Получить список расписаний"""
    cache_key = f"schedules:{date if date else 'all'}"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    query = models.Schedule.select()
    
    if date:
        query = query.where(models.Schedule.date == date)
    
    query = query.order_by(
        models.Schedule.date.asc(), 
        models.Schedule.update_at.asc()
    )
    

    schedules = await DB.aio_execute(query)

    result = {
        'count': len(schedules),
        'entities': [schedule.to_dict() for schedule in schedules]
    }
    
    if redis_client:
        redis_client.setex(
            cache_key,
            1800,
            json.dumps(result, default=str)
        )
    
    return result


async def get_dict_by_schedule(
    schedule: models.Schedule,
    group: models.Group = None
):
    """Получить полное расписание"""
    cache_key = f"schedule_lessons:{schedule_id}:{group if group else 'all'}"

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    schedule = await DB.aio_execute(models.Schedule.filter(id=schedule_id).first())
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

    if redis_client:
        redis_client.setex(
            cache_key,
            1800,
            json.dumps(result, default=str)
        )
    
    return result


@app.get('/schedule/{schedule_id}/')
async def get_schedule(schedule_id: int, group_id: int = None):
    """Получение расписания по дисциплине"""
    cache_key = f"schedule_by_id:{schedule_id}:{group_id if group_id else 'all'}"
    
    try:
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode cached data for key: {cache_key}")

    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")

    try:
        schedule = await models.Schedule.aio_get(id=schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail="Расписание с указанным ID не найдено"
            )
        
        group = await models.Group.aio_get(id=group_id) if group_id else None
        result = await get_dict_by_schedule(schedule=schedule, group=group)
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении данных из базы"
        )
    
    try:
        if redis_client:
            redis_client.setex(
                cache_key,
                3600,  # 1 час
                json.dumps(result, ensure_ascii=False, default=str)
            )
    except redis.RedisError as e:
        logger.error(f"Failed to cache data: {str(e)}")
    
    return result


@app.get('/schedule/date/{date}/')
async def get_schedule_by_date(date: Date, group_id: int = None):
    """Получение расписания по конкретной дате"""
    cache_key = f"schedule:{date.isoformat()}:{group_id if group_id else 'all'}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    schedule = await models.Schedule.aio_get_or_none(date=date)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Расписание на указанную дату не найдено"
        )
    
    group = await models.Group.aio_get(id=group_id) if group_id else None
    result = await get_dict_by_schedule(schedule=schedule, group=group)
    redis_client.setex(
        cache_key,
        3600,
        json.dumps(result, ensure_ascii=False, default=str)
    )
    
    return result


@app.get("/schedule/teacher/{teacher_id}")
async def get_teacher_schedule(teacher_id: int):
    """Получение расписания преподавателя"""
    cache_key = f"teacher_schedule:{teacher_id}"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    disciplines = await Discipline.aio_filter(teacher__user_id=teacher_id)
    if not disciplines:
        raise HTTPException(
            status_code=404,
            detail="Преподаватель не найден или у него нет дисциплин"
        )

    lessons = await Lesson.aio_filter(
        discipline__in=[d.id for d in disciplines],
        arhiv=False
    ).prefetch_related('schedule', 'group', 'discipline', 'auditory')
    
    response = []
    for lesson in lessons:
        response.append({
            "date": lesson.schedule.date.isoformat(),
            "group_name": lesson.group.name,
            "pair": lesson.pair,
            "discipline_name": lesson.discipline.name,
            "auditory_name": lesson.auditory.name,
            "lesson_id": lesson.id
        })
    redis_client.setex(
        cache_key,
        3600,
        json.dumps(response, ensure_ascii=False, default=str)
    )
    
    return response


@app.get('/date/{id}')
async def get_date_doc(id: int):
    """По айди возвращает дату"""
    cache_key = f"date:{id}"
    cached_date = redis_client.get(cache_key)
    
    if cached_date:
        return {'date': cached_date}
    
    schedule = await models.Schedule.aio_get(id=id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"Расписание с ID {id} не найдено"
        )

    date_iso = schedule.date.isoformat()
    redis_client.setex(
        cache_key,
        86400,
        date_iso
    )
    
    return {'date': date_iso}

@app.get('/groups/')
async def get_groups():
    """Получить список групп"""
    cache_key = "all_groups"

    try:
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode cached groups data: {str(e)}")
    except redis.RedisError as e:
        logger.error(f"Redis error while getting groups: {str(e)}")
    try:
        groups = await DB.aio_execute(models.Group.select())
        
        result = {
            'count': len(groups),
            'entities': [group.to_dict() for group in groups],
        }
        
    except Exception as e:
        logger.error(f"Database error while fetching groups: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении списка групп из базы данных"
        )
    
    try:
        if redis_client:
            redis_client.setex(
                cache_key,
                86400,
                json.dumps(result, ensure_ascii=False, default=str)
            )
    except redis.RedisError as e:
        logger.error(f"Failed to cache groups data: {str(e)}")
    
    return result


@app.get('/group/{group_id}/')
async def get_group_by_id(group_id: int):
    """Получить группу"""

    cache_key = f"group_schedules:{group_id}"
    
    try:
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode cached group schedules: {str(e)}")
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")
    try:
        group = await models.Group.aio_get(id=group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")

        lessons = await DB.aio_execute(
            group.lessons.group_by(models.Lesson.schedule)
        )
        
        current_date = Date.today()
        schedules = [
            lesson.schedule.to_dict() 
            for lesson in lessons 
            if lesson.schedule and lesson.schedule.date >= current_date
        ]
        
        result = {
            **group.to_dict(),
            'schedules': {
                'count': len(schedules),
                'entities': schedules
            }
        }
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении расписания группы"
        )

    try:
        if redis_client:
            redis_client.setex(
                cache_key,
                3600,
                json.dumps(result, ensure_ascii=False, default=str)
            )
    except redis.RedisError as e:
        logger.error(f"Failed to cache group schedules: {str(e)}")
    return result


@app.get('/disciplines/')
async def get_discipline():
    """Получить список дисциплин"""
    cache_key = "all_disciplines"
    
    try:
        if redis_client:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode cached disciplines: {str(e)}")
    except Exception as e:
        logger.error(f"Redis error: {str(e)}")

    try:
        disciplines = await DB.aio_execute(models.Discipline.select())
        
        result = {
            'count': len(disciplines),
            'entities': [discipline.to_dict() for discipline in disciplines],
        }
        try:
            if redis_client:
                await redis_client.setex(
                    cache_key,
                    86400,
                    json.dumps(result, ensure_ascii=False, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to cache disciplines: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении списка дисциплин"
        )


@app.get('/discipline/{discipline_id}/')
async def get_discipline_by_id(discipline_id: int):
    """Получить дисциплину"""
    current_date = Date.today().isoformat()
    cache_key = f"discipline_schedules:{discipline_id}:{current_date}"
    try:
        if redis_client:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode cached discipline schedules: {str(e)}")
    except Exception as e:
        logger.error(f"Redis error: {str(e)}")
    
    try:
        discipline = await models.Discipline.aio_get(id=discipline_id)
        if not discipline:
            raise HTTPException(status_code=404, detail="Дисциплина не найдена")

        lessons = await DB.aio_execute(
            models.Lesson.select()
            .where(
                (models.Lesson.discipline == discipline) &
                (models.Lesson.schedule.date >= Date.today())
            )
            .join(models.Schedule)
            .group_by(models.Lesson.schedule)
        )
        
        result = {
            **discipline.to_dict(),
            'schedules': {
                'count': len(lessons),
                'entities': [lesson.schedule.to_dict() for lesson in lessons]
            }
        }
        
        try:
            if redis_client:
                await redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(result, ensure_ascii=False, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to cache discipline schedules: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении расписания дисциплины"
        )


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
    cache_key = f"schedule_group:{schedule_id}:{group_id if group_id else 'all'}"
    а
    try:
        if redis_client:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode cached schedule data: {str(e)}")
    except Exception as e:
        logger.error(f"Redis error: {str(e)}")
    
    try:
        schedule, group = await asyncio.gather(
            models.Schedule.aio_get(id=schedule_id),
            models.Group.aio_get(id=group_id) if group_id else asyncio.sleep(0)
        )
        
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail="Расписание не найдено"
            )
            
        if group_id and not group:
            raise HTTPException(
                status_code=404,
                detail="Группа не найдена"
            )
        
        result = await get_dict_by_schedule(
            schedule=schedule,
            group=group
        )
        
        try:
            if redis_client:
                await redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(result, ensure_ascii=False, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to cache schedule data: {str(e)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении данных расписания"
        )


@app.get("/schedule/teacher/{teacher_id}")
async def get_teacher_schedule(teacher_id: int):
    """Получение преподавателя по его айди

    Args:
        teacher_id (int): [teacher id or user id]

    Raises:
        HTTPException: [404]

    Returns:
        [response]: [date,group_name,pair,discipline_name,auditory_name]
    """
    # Получаем дисциплины преподавателя
    disciplines = await Discipline.aio_filter(teacher__user_id=teacher_id)
    if not disciplines:
        raise HTTPException(
            status_code=404,
            detail="Преподаватель не найден или у него нет дисциплин"
            )

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