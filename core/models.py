"""Модели"""
from datetime import datetime
import mysql.connector
import peewee
from peewee_async import PooledMySQLDatabase, AioModel


DB_NAME = "raspisane"
DB_CONFIG = {
    "user": "root",
    "password": "3010",
    "host": "127.0.0.1",
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

async def update_schedule(date: datetime, doc_id: str, schedule_data: dict):
    """Проверка на изменения в расписании и возврат новых объектов"""

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