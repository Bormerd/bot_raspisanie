# redis_cache.py
import redis
import json
import os
from typing import Dict, List, Union
from core import models
from playhouse.shortcuts import model_to_dict

class RedisCache:
    """Класс для работы с Redis, включая копирование БД"""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
        )

        self.DB_COPY_EXPIRE = 1800

    async def copy_table(self, model: str):
        """Копирует конкретную таблицу в Redis"""
        models_map = {
            'user': models.User,
            'student': models.Student,
            'teacher': models.Teacher,
            'group': models.Group,
            'discipline': models.Discipline,
            'schedule': models.Schedule,
            'lesson': models.Lesson
        }
        
        if model not in models_map:
            raise ValueError(f"Модель {model} не поддерживается")
        
        records = models_map[model].select()
        with self.redis.pipeline() as pipe:
            for record in records:
                pipe.setex(
                    f"{model}:{record.id}", 
                    self.DB_COPY_EXPIRE,
                    json.dumps(model_to_dict(record), default = str )
                )
            pipe.execute()

    # async def get_cached_table(self, model: str) -> List[Dict]:
    #     """Получает копию таблицы из Redis"""
    #     keys = self.redis.keys(f"{model}:*")
    #     return [json.loads(self.redis.get(key)) for key in keys]

    # async def sync_record(self, model: str, record_id: int):
    #     """Синхронизирует одну запись с БД"""
    #     models_map = {
    #         'user': User,
    #         'student': Student,
    #         # ... остальные модели
    #     }
    #     record = await models_map[model].aio_get(id=record_id)
    #     self.redis.setex(
    #         f"{model}:{record_id}",
    #         self.DB_COPY_EXPIRE,
    #         record.to_json()
    #     )

    # def clear_cache(self):
    #     """Очищает весь кэш"""
    #     self.redis.flushdb()
