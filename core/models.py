"""Модели"""
from datetime import datetime
import mysql.connector
import peewee
from peewee_async import PooledMySQLDatabase, AioModel


DB_NAME = "raspisan"
DB_CONFIG = {
    "user": "root",
    "password": "3010",
    "host": "localhost",
    "port": 3306,
}
# Если БД нет, запустить модуль
DB = PooledMySQLDatabase(DB_NAME, **DB_CONFIG, max_connections=20)


class BaseModel(AioModel):
    """Базовая модель"""

    def to_dict(self):
        """Преобразовать в словарь"""
        # pylint: disable=no-member
        result = {}
        for field in self._meta.fields:
            value = getattr(self, field)

            if isinstance(value, BaseModel):
                result[field] = value.to_dict()
            else:
                result[field] = value
        return result

    class Meta:
        """Подключение к БД"""
        database = DB

class User(BaseModel):
    """Расписание"""
    chat_id = peewee.IntegerField()


class Schedule(BaseModel):
    """Расписание"""
    date = peewee.DateField()
    update_at = peewee.DateTimeField()
    doc_id = peewee.CharField()


class Group(BaseModel):
    """Группа"""
    name = peewee.CharField()


class Discipline(BaseModel):
    """Дисциплина"""
    name = peewee.CharField()


class Auditory(BaseModel):
    """Аудитория"""
    name = peewee.CharField()


class Lesson(BaseModel):
    """Занятие"""
    schedule = peewee.ForeignKeyField(
        Schedule,
        backref='lessons',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    group = peewee.ForeignKeyField(
        Group,
        backref='lessons',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    discipline = peewee.ForeignKeyField(
        Discipline,
        backref='lessons',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    auditory = peewee.ForeignKeyField(
        Auditory,
        backref='lessons',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    pair = peewee.IntegerField()
    arhiv = peewee.BooleanField(default=False)
    old_lesson = peewee.ForeignKeyField(
        'self',
        null=True,
        on_delete="CASCADE",
        on_update="CASCADE"
    )

    def __str__(self):
        return (f"{self.schedule.date} {self.group.name} {self.pair} "
                f"{self.discipline.name} {self.auditory.name}")

class Student(BaseModel):
    """Модель связи между пользователями и группами"""
    user_id = peewee.ForeignKeyField(
        User, 
        backref='group',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    group_id = peewee.ForeignKeyField(
        Group, 
        backref='user',
        on_delete="CASCADE",
        on_update="CASCADE"
    )
    @classmethod
    async def aio_filter(cls, *args, **kwargs):
        """Асинхронный аналог filter()"""
        return await DB.aio_execute(cls.filter(*args, **kwargs))

class Teacher(BaseModel):
    """Модель связи между пользователями и дисциплинами"""
    user_id = peewee.ForeignKeyField(
        User, 
        backref='disciplines',
        on_delete="CASCADE",
        on_update="CASCADE"
        )
    discipline_id = peewee.ForeignKeyField(
        Discipline, 
        backref='user',
        on_delete="CASCADE",
        on_update="CASCADE"
        )

async def check_schedule_changes(date: datetime, doc_id: str, schedule_data: dict):
    """Проверка изменений в расписании и возврат списка изменений"""
    changes = {
        'new_lessons': [],
        'updated_lessons': [],
        'deleted_lessons': []
    }
    
    # Поиск существующего расписания
    schedule = await Schedule.aio_get_or_none(date=date, doc_id=doc_id)
    
    if schedule is None:
        # Все занятия новые, если расписания не было
        for group_name, group_d in schedule_data.items():
            group = await Group.aio_get_or_create(name=group_name)
            for pair, lesson_d in group_d.items():
                changes['new_lessons'].append({
                    'group': group_name,
                    'pair': pair,
                    'discipline': lesson_d['discipline'],
                    'auditory': lesson_d.get('auditory', '')
                })
        return changes
    
    # Собираем существующие занятия
    existing_lessons = {}
    lessons = await DB.aio_execute(
        Lesson.select().where(
            (Lesson.schedule == schedule) &
            (Lesson.arhiv == False)
        )
    )
    
    for lesson in lessons:
        key = f"{lesson.group.name}_{lesson.pair}"
        existing_lessons[key] = {
            'discipline': lesson.discipline.name,
            'auditory': lesson.auditory.name,
            'lesson_obj': lesson
        }
    
    # Проверяем изменения
    for group_name, group_d in schedule_data.items():
        group = await Group.aio_get_or_create(name=group_name)
        for pair, lesson_d in group_d.items():
            key = f"{group_name}_{pair}"
            if key not in existing_lessons:
                # Новое занятие
                changes['new_lessons'].append({
                    'group': group_name,
                    'pair': pair,
                    'discipline': lesson_d['discipline'],
                    'auditory': lesson_d.get('auditory', '')
                })
            else:
                # Проверяем изменения в существующем занятии
                existing = existing_lessons[key]
                if (existing['discipline'] != lesson_d['discipline'] or 
                    existing['auditory'] != lesson_d.get('auditory', '')):
                    changes['updated_lessons'].append({
                        'old': existing,
                        'new': {
                            'group': group_name,
                            'pair': pair,
                            'discipline': lesson_d['discipline'],
                            'auditory': lesson_d.get('auditory', '')
                        }
                    })
                del existing_lessons[key]
    
    # Оставшиеся в existing_lessons - удаленные занятия
    for key, lesson in existing_lessons.items():
        changes['deleted_lessons'].append({
            'group': key.split('_')[0],
            'pair': key.split('_')[1],
            'discipline': lesson['discipline'],
            'auditory': lesson['auditory']
        })
    
    return changes

async def update_schedule(date: datetime, doc_id: str, schedule_data: dict):
    """Проверка на изменения в расписании и возврат новых объектов"""
    changes = await check_schedule_changes(date, doc_id, schedule_data)

    # Поиск или создание расписания
    schedule = await Schedule.aio_get_or_none(
        date=date,
        doc_id=doc_id
    )

    if schedule is None:
        schedule = await Schedule.aio_create(
            date=date, 
            doc_id=doc_id,
            update_at=datetime.now(),
        )

    for group_name, group_d in schedule_data.items():
        # Поиск или создание группы
        group, _ = await Group.aio_get_or_create(name=group_name)

        for pair, lesson_d in group_d.items():
            # Поиск или создание дисциплины
            discipline, _ = await Discipline.aio_get_or_create(
                name=lesson_d['discipline']
            )

            # Поиск или создание аудитории
            auditory, _ = await Auditory.aio_get_or_create(
                name=lesson_d.get('auditory', '')
            )

            # Поиск старого занятия
            old_lesson = await Lesson.aio_get_or_none(
                schedule=schedule,
                group=group,
                pair=pair,
                arhiv=False
            )
            if old_lesson:
                new_lesson, created = await Lesson.aio_get_or_create(
                    pair=pair,
                    schedule=schedule,
                    auditory=auditory,
                    discipline=discipline,
                    group=group
                )
                if created:
                    new_lesson.old_lesson = old_lesson
                    await new_lesson.aio_save()
                    old_lesson.arhiv = True
                    await old_lesson.aio_save()
            else:
                new_lesson = await Lesson.aio_create(
                    pair=pair,
                    schedule=schedule,
                    auditory=auditory,
                    discipline=discipline,
                    group=group
                )
    return changes

if __name__ == "__main__":
    with mysql.connector.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;")
        DB = PooledMySQLDatabase(DB_NAME, **DB_CONFIG, max_connections=20)
    with DB:
        DB.create_tables(
            [User, Schedule, Group, Discipline, Auditory, Lesson, Teacher, Student],
            safe=True
        )
    print("Tables are created.")