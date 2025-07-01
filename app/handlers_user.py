import re
import os
import time
import asyncio
import textwrap
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ContentType, ReplyKeyboardRemove
from app.keyboards_user import *
from get_data.car_search import search_car_number
from plate_detection.detection import detect
from plate_detection.plate_reader import read_number
from utils.utils import download_photo, update_process_message
from database.database_cars import get_description, add_description
from gigachat.gigachat_api import send_promt


router = Router()


@router.message(CommandStart())
async def send_start_message(message: Message):
    start_message = """
                    <b>Привет! 👋
                    Я нахожу информацию по машинам!</b> 🚗\n
                    Чтобы найти информацию по автомобилю отправь мне его фотографию. 📷\n
                    <b>ВАЖНО:</b> на фотографии должен быть четко виден номер машины❗️\n
                    Также, ты можешь написать вручную номер автомобиля в формате: <b>А123АА45</b>.\n
                    При таком варианте, данные обработаются быстрее и ответ придет раньше, чем при использовании фотографии.⏳
                    Также, этот вариант исключает неправильное определение номера.\n
                    <b>Приятного пользования</b> 😊
                    """
    start_message = textwrap.dedent(start_message)
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await message.answer(start_message, reply_markup=await admin_button())
    else:
        await message.answer(start_message)



@router.message(F.text)
async def send_car_info(message: Message, found_number=None):
    start_time = time.time()

    # Если номер передан, используем его. Если нет, то берем из сообщения.
    text_number = found_number if found_number else message.text.replace(' ', '').upper()
    
    pattern = r"^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$"
    if re.fullmatch(pattern, text_number):

        process_message = await message.answer(
            f"✅ Найден номер: <b>{text_number}</b>\n\n⏳ Ищу информацию по машине. . ."
            if found_number else "⏳ Ищу информацию по машине. . ."
        )
        update_task = asyncio.create_task(update_process_message(process_message, text_number))
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    result = await search_car_number(text_number)
    # Формируем ответ
    if isinstance(result, dict):
        message_info = f"<b>Информация по машине с номером: {text_number}</b>\n"
        
        if result['brand'] != "" and result['model'] != "":
            message_info += f"\nМодель: <b>{result['brand']} {result['model']}</b>"

        if result['year'] != "":
            message_info += f"\nГод: <b>{result['year']}</b>"
            
        if result['volume'] != "":
            message_info += f"\nОбъем двигателя: <b>{result['volume']} куб. см.</b>"

        if result['power'] != "":
            message_info += f"\nМощность двигателя: <b>{result['power']} л. с.</b>"

        if result["color"] != "":
            message_info += f"\nЦвет: <b>{result['color']}</b>"
        
        if "min_price" in result:
            message_info += f"\n\nМинимальная стоимость: <b>{result['min_price']} ₽</b>\nСредняя стоимость: <b>{result['avg_price']} ₽</b>"
            message_info += f"\n\n<a href='{result['url']}'>Посмотреть на drom.ru</a>"

        message_info = textwrap.dedent(message_info)

        response_time = time.time() - start_time
        if response_time < 3:
            overtime = 3 - response_time
            await asyncio.sleep(overtime)

        update_task.cancel()
        await process_message.delete()
        await message.answer(message_info, reply_markup=await description_button())
    else:
        try:
            await process_message.delete()
        except UnboundLocalError:
            pass
        await message.answer(result)



@router.message(F.photo)
async def photo_processing(message: Message):
    process_message = await message.answer("🔎 Ищу номер на фото. . .", reply_markup=ReplyKeyboardRemove())
    await message.bot.send_chat_action(message.chat.id, "typing")
    photo_path = await download_photo(message)
    crop_number = await detect(photo_path, message.from_user.username)
    if crop_number:
        carplate = await read_number(crop_number)
        if carplate:
            await process_message.delete()
            await send_car_info(message, found_number=carplate)  
        else:
            await process_message.delete()
            await message.answer("⛔ Не удалось определить номер.\n\n➡️ Попробуйте написать номер вручную.")
    else:
        await process_message.delete()
        await message.answer("⛔ Не удалось найти номер на фото.\n\n➡️ Попробуйте написать номер вручную.")



@router.callback_query(F.data == "description")
async def send_description(callback: CallbackQuery):
    await callback.answer()
    bot = callback.message.bot
    process_message = await callback.message.answer("⏳ Формирую описание. . .")
    await bot.send_chat_action(callback.message.chat.id, "typing")
    try:
        text = callback.message.text

        model_pattern = r"Модель:\s(.*?)\s(.*?)\n"
        year_pattern = r"Год:\s(\d{4})"
        brand = re.search(model_pattern, text).group(1)
        model = re.search(model_pattern, text).group(2)
        year = re.search(year_pattern, text).group(1)

        data_car = {"brand": brand, "model": model, "year": year}
        # Проверяем наличие описания в базе
        await asyncio.sleep(3)
        text_description = await get_description(data_car)
        # Если описания в базе нет, то генерируем его и добавляем в базу
        if not text_description:
            text_description = await send_promt(data_car)
            await add_description(data_car, text_description)
        # Отправляем описание пользователю
        await process_message.delete()
        await callback.message.answer(text_description)
    except:
        await process_message.delete()
        await callback.message.answer("😔 Не удалось сформировать описание")



@router.message(~F.content_type.in_({ContentType.TEXT, ContentType.PHOTO}))
async def handle_unsupported_content(message: Message):
    await message.answer(
        "⚠️ Извините, но я пока не умею работать с этим типом сообщений.\n\n➡️ Попробуйте отправить текст или фотографию автомобиля."
    )