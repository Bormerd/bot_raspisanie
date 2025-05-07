from datetime import datetime
from aiogram import Bot
from typing import Dict, List
from core.models import User, Student, Teacher, Group, Discipline
from RequestsUrl import service

async def send_schedule_updates(bot: Bot, changes: Dict, date: datetime):
    """Отправка уведомлений об изменениях в расписании"""
    if not any(changes.values()):
        return
    
    date_str = date.strftime("%Y-%m-%d")
    
    # Отправка уведомлений студентам
    affected_groups = set()
    for change_type in changes.values():
        for change in change_type:
            affected_groups.add(change['group'])
    
    for group_name in affected_groups:
        group = await Group.aio_get_or_none(name=group_name)
        if not group:
            continue
            
        students = await Student.aio_filter(group_id=group)
        for student in students:
            user = await User.aio_get(id=student.user_id)
            if not user:
                continue
                
            message = f"🔔 Изменения в расписании на {date_str} для группы {group_name}:\n"
            
            if changes['new_lessons']:
                message += "\n📌 Новые занятия:\n"
                for lesson in [l for l in changes['new_lessons'] if l['group'] == group_name]:
                    message += f"{lesson['pair']}) {lesson['discipline']} ({lesson['auditory']})\n"
            
            if changes['updated_lessons']:
                message += "\n🔄 Измененные занятия:\n"
                for lesson in [l['new'] for l in changes['updated_lessons'] if l['new']['group'] == group_name]:
                    old = next(l['old'] for l in changes['updated_lessons'] 
                             if l['new']['group'] == group_name and l['new']['pair'] == lesson['pair'])
                    message += (f"{lesson['pair']}) {old['discipline']} ({old['auditory']}) → "
                              f"{lesson['discipline']} ({lesson['auditory']})\n")
            
            if changes['deleted_lessons']:
                message += "\n❌ Отмененные занятия:\n"
                for lesson in [l for l in changes['deleted_lessons'] if l['group'] == group_name]:
                    message += f"{lesson['pair']}) {lesson['discipline']} ({lesson['auditory']})\n"
            
            try:
                await bot.send_message(user.chat_id, message)
            except Exception as e:
                print(f"Ошибка отправки уведомления студенту {user.chat_id}: {e}")
    
    # Отправка уведомлений преподавателям
    affected_disciplines = set()
    for change_type in changes.values():
        for change in change_type:
            affected_disciplines.add(change['discipline'])
    
    for discipline_name in affected_disciplines:
        discipline = await Discipline.aio_get_or_none(name=discipline_name)
        if not discipline:
            continue
            
        teachers = await Teacher.aio_filter(discipline_id=discipline)
        for teacher in teachers:
            user = await User.aio_get(id=teacher.user_id)
            if not user:
                continue
                
            message = f"🔔 Изменения в расписании на {date_str} по дисциплине {discipline_name}:\n"
            
            if changes['new_lessons']:
                message += "\n📌 Новые занятия:\n"
                for lesson in [l for l in changes['new_lessons'] if l['discipline'] == discipline_name]:
                    message += f"{lesson['pair']}) Группа {lesson['group']} ({lesson['auditory']})\n"
            
            if changes['updated_lessons']:
                message += "\n🔄 Измененные занятия:\n"
                for lesson in [l['new'] for l in changes['updated_lessons'] if l['new']['discipline'] == discipline_name]:
                    old = next(l['old'] for l in changes['updated_lessons'] 
                             if l['new']['discipline'] == discipline_name and l['new']['pair'] == lesson['pair'])
                    message += (f"{lesson['pair']}) Группа {lesson['group']}: "
                              f"{old['discipline']} ({old['auditory']}) → "
                              f"{lesson['discipline']} ({lesson['auditory']})\n")
            
            if changes['deleted_lessons']:
                message += "\n❌ Отмененные занятия:\n"
                for lesson in [l for l in changes['deleted_lessons'] if l['discipline'] == discipline_name]:
                    message += f"{lesson['pair']}) Группа {lesson['group']} ({lesson['auditory']})\n"
            
            try:
                await bot.send_message(user.chat_id, message)
            except Exception as e:
                print(f"Ошибка отправки уведомления преподавателю {user.chat_id}: {e}")