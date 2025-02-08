import logging
import os
import io
import random
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Импорт функций и классов из main.py
from main import lifespan, get_schedules, get_schedule, get_groups, get_group_by_id, get_discipline, get_discipline_by_id

load_dotenv(".env")

bot_token = os.getenv("BOT_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=bot_token)
dp = Dispatcher()

# Путь к вашему файлу credentials.json
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Аутентификация
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# ID файла на Google Диске
FILE_ID = '1Kyvu7G2Gu72FrsWOocGliknataRUcYS4'  # Замените на реальный ID файла

# Запуск FastAPI в фоновом режиме
app = FastAPI(lifespan=lifespan)

@app.get("/schedules/")
async def schedules():
    return await get_schedules()

@app.get("/schedule/{schedule_id}/")
async def schedule(schedule_id: int, group_id: int = None):
    return await get_schedule(schedule_id, group_id)

@app.get("/groups/")
async def groups():
    return await get_groups()

@app.get("/group/{group_id}/")
async def group(group_id: int):
    return await get_group_by_id(group_id)

@app.get("/disciplines/")
async def disciplines():
    return await get_discipline()

@app.get("/discipline/{discipline_id}/")
async def discipline(discipline_id: int):
    return await get_discipline_by_id(discipline_id)

# Запуск FastAPI в фоновом режиме
async def run_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Расписание"), KeyboardButton(text="Привет")],
            [KeyboardButton(text="Звонки"), KeyboardButton(text="Id")]
        ],
        resize_keyboard=True
    )
    await message.answer("Посмотри что я могу", reply_markup=markup)

# Обработчик текстовых сообщений
@dp.message(F.text == "Id")
async def get_user_id(message: types.Message):
    await message.answer(f"Твой ID: {message.from_user.id}", parse_mode="HTML")

@dp.message(F.text == "Звонки")
async def send_bells_photo(message: types.Message):
    photo = types.FSInputFile("Звонки.png")
    await message.answer_photo(photo)

# Обработчик для обработки файла по запросу "Расписание"
@dp.message(F.text == "Расписание")
async def handle_schedule_request(message: types.Message):
    try:
        # Получаем расписание из API
        response = requests.get("http://localhost:8000/schedules/")
        if response.status_code == 200:
            schedule_data = response.json()
            # Форматируем расписание для отправки
            schedule_text = "Расписание:\n"
            for entity in schedule_data['entities']:
                schedule_text += f"{entity['date']}: {entity['update_at']}\n"
            # Отправляем расписание пользователю
            await message.answer(schedule_text, parse_mode="HTML")
        else:
            await message.answer("Не удалось получить расписание", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        await message.answer(f"Произошла ошибка: {e}")

@dp.message(F.text == "Привет")
async def say_hello(message: types.Message):
    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>", parse_mode="HTML")

@dp.message(F.text)
async def unknown_message(message: types.Message):
    await message.answer("Я тебя не понимаю", parse_mode="HTML")

# Обработчик фото
@dp.message(F.photo) 
async def get_user_photo(message: types.Message): 
    phrases = [ "Зачёт", "Ну такое",
               "Может ещё какие варианты есть", "Одобряю" ] 
    rp = random.choice(phrases) 
    await message.answer(rp, parse_mode="HTML")
    
async def main(): 
    # Запуск FastAPI в фоновом режиме
    asyncio.create_task(run_fastapi())
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())