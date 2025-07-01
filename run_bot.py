import os
import asyncio
import aiofiles
import logging
import datetime
import platform
import config.config as cfg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.methods import DeleteWebhook
from dotenv import load_dotenv
from io import StringIO
from app.handlers_user import router
from app.handlers_admin import router2
from database.create_tables import create_tables_db
from utils.utils import get_memory_info

log_stream = StringIO()


def init():
    global bot, dp

    # Определение пути к .env
    if os.path.exists("config/.env"):
        env_path = "config/.env"
    elif os.path.exists("config/.env.example"):
        env_path = "config/.env.example"
    else:
        raise FileNotFoundError("Файл .env или .env.example не найден")

    # Загрузка переменных окружения
    load_dotenv(env_path)

    TOKEN = os.getenv("TOKEN")
    if TOKEN == "":
        raise RuntimeError(f"Отсутствует значение TOKEN в {env_path}")

    # Инициализация БД, если файла нет
    if not os.path.exists("database/cars_database.db"):
        print("Создание БД...")
        asyncio.run(create_tables_db())

    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Логирование
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[logging.StreamHandler(log_stream)]
    )


async def write_logs(text: str):
    current_time = datetime.datetime.now().strftime("%d.%m.%y %H:%M")
    text = f"{current_time} {text}"
    async with aiofiles.open("bot_logs.log", "a", encoding="utf-8") as log_file:
        if text == "Перезапуск бота...":
            await log_file.write(f"{text}\n")
        else:
            await log_file.write(f"\n{text}\n")


async def monitor_logs():
    """
    Мониторинг логов для проверки появления строки "Failed".
    Если строка найдена, перезапускаем функцию main.
    """
    global current_main_task
    while True:
        await asyncio.sleep(5)  # Проверяем каждые 5 секунд
        log_content = log_stream.getvalue()
        if "Failed" in log_content:
            await write_logs(log_content)
            # Отмена текущей задачи main, если она выполняется
            if current_main_task and not current_main_task.done():
                current_main_task.cancel()
                try:
                    await current_main_task
                except asyncio.CancelledError:
                    pass
            # Запускаем новый main
            await write_logs("Перезапуск бота...")
            current_main_task = asyncio.create_task(main())
            await write_logs("Бот включен")
        # Очищаем логи
        log_stream.truncate(0)
        log_stream.seek(0)


async def monitor_memory():
    """Мониторинг использования памяти каждые 12 часов."""
    while True:
        memory_info = get_memory_info()
        print(memory_info + "\n")
        async with aiofiles.open("bot_logs.log", "a", encoding="utf-8") as file:
            await file.write(f"\n{memory_info}\n")
        
        await asyncio.sleep((60 * 60) * 12)


async def main():
    await bot(DeleteWebhook(drop_pending_updates=False))
    dp.include_router(router2)
    dp.include_router(router)
    await write_logs("Бот включен")
    print("Бот включен")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        raise


async def run():
    """Основной цикл для запуска main и мониторинга логов."""
    global current_main_task

    current_main_task = asyncio.create_task(main())  # Запускаем main и мониторинг логов
    asyncio.create_task(monitor_memory())  # Запускаем мониторинг памяти
    await monitor_logs()  # Блокирует выполнение, пока мониторинг активен


def start():
    try:
        init()
        if platform.system() == "Linux":
            answer = input("Запуск на сервере? (y/n): ")
            cfg.is_server = (answer == "y")
        asyncio.run(run())
    except KeyboardInterrupt:
        current_time = datetime.datetime.now().strftime("%d.%m.%y %H:%M")
        print(f"{current_time} Бот выключен")
        with open("bot_logs.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"{current_time} Бот выключен")


if __name__ == "__main__":
    start()

