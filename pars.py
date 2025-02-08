import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from dotenv import load_dotenv
import asyncio
from docx import Document
import pandas as pd
import io
import random
import requests
import os


load_dotenv(".env")

bot_token = os.getenv("BOT_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=bot_token)
dp = Dispatcher()

# Прямая ссылка на .docx файл
FILE_URL = "https://docs.google.com/document/d/1aA9lX1n59qsubeP470RRc4telh3O0Tqf/edit"  # Замените на реальную ссылку

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
        # Загрузка файла по ссылке
        response = requests.get(FILE_URL)
        if response.status_code != 200:
            await message.answer("Не удалось загрузить файл. Проверьте ссылку.")
            return

        # Проверка, что файл действительно .docx
        if not response.headers.get('Content-Type', '').lower() == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            await message.answer("Файл не является .docx документом.")
            return

        # Преобразование файла
        file_io = io.BytesIO(response.content)
        doc = Document(file_io)
        data = []
        for table in doc.tables:
            for row in table.rows:
                data.append([cell.text for cell in row.cells])

        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)

        # Отправка файла пользователю
        await message.answer_document(types.InputFile(excel_file, filename="schedule.xlsx"))

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
    phrases = [
        "Зачёт",
        "Ну такое",
        "Может ещё какие варианты есть",
        "Одобряю"
    ]
    rp = random.choice(phrases)
    await message.answer(rp, parse_mode="HTML")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())