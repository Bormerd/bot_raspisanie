"""Модуль для запуска"""
import os
import asyncio
from aiogram import Bot,Dispatcher
from dotenv import load_dotenv
from bot.handlers.handlers import function
import uvicorn
import api

load_dotenv(".env")
bot=os.getenv('bot')
bot=Bot(token=bot)
dp = Dispatcher()
app = api.app

# Функция для запуска FastAPI
async def start_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

# Функция для запуска бота
async def start_bot():
    """Запуск бота"""
    try:
        function(dp)  # Регистрация обработчиков
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

# Основная функция для запуска обоих приложений
async def main():
    await asyncio.gather(
        start_fastapi(),
        start_bot(),
    )

# Точка входа
if __name__ == '__main__':
    asyncio.run(main())
