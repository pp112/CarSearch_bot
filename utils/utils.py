import os
import time
import asyncio
import aiofiles
import datetime
import psutil
from aiogram.types import Message


def get_memory_info():
    memory = psutil.virtual_memory()
    current_time = datetime.datetime.now().strftime("%d.%m.%y %H:%M")
    memory_info = (
        f"{current_time} - Всего памяти: {memory.total / 1024**2:.0f} Мб\n"
        f"{current_time} - Используется: {memory.used / 1024**2:.0f} Мб\n"
        f"{current_time} - Свободно: {memory.available / 1024**2:.0f} Мб"
    )
    return memory_info


async def write_file_logs(text, print_terminal=False):
    async with aiofiles.open("bot_logs.log", "a", encoding="utf-8") as file:
        await file.write(text + "\n")
    if print_terminal:
        print(text)


async def update_process_message(process_message: Message, carplate):
    symbols = ["⌛️", "⏳"]
    index = 0
    first_text = f"✅ Найден номер: <b>{carplate}</b>\n\n" if "Найден номер" in process_message.text else ""
    try:
        while True:
            await asyncio.sleep(1.55)
            new_text = f"{first_text}{symbols[index % len(symbols)]} Ищу информацию по машине. . ."
            await process_message.edit_text(new_text)
            index += 1
    except asyncio.CancelledError:
        pass


async def download_photo(message: Message) -> str:
    # Загружаем файл
    bot = message.bot
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file.file_path)
    downloaded_file = downloaded_file.getvalue()

    # Путь для сохранения фото
    folder_name = r"images/user_photos/"
    os.makedirs(folder_name, exist_ok=True)
    photo_path = f"{folder_name}/photo_{message.from_user.username}.jpg"
    # Сохраняем фото
    async with aiofiles.open(photo_path, "wb") as file:
        await file.write(downloaded_file)

    return photo_path


def measure_time(func):
    async def wrapper(message: Message, **kwargs):
        start_time = time.time()  # Засекаем время начала выполнения
        filtered_kwargs = {key: value for key, value in kwargs.items() if key == 'found_number'}
        result = await func(message, **filtered_kwargs)  # Выполняем функцию
        end_time = time.time()  # Засекаем время окончания выполнения
        elapsed_time = round(end_time - start_time, 2)  # Рассчитываем длительность
        await message.answer(f"Время ответа: <b>{elapsed_time} с.</b>")
        return result
    return wrapper