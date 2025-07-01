import re
import os
import json
import aiosqlite
import aiofiles
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.keyboards_admin import *
from app.handlers_user import send_start_message
from utils.utils import get_memory_info


router2 = Router()

class Admin(StatesGroup):
    admin_panel = State()
    editing_json = State()
    adding_value_json = State()
    show_db = State()
    editing_db = State()
    del_data_db = State()
    view_logs = State()


@router2.message(CommandStart())
async def restart(message: Message, state: FSMContext):
    await state.clear()
    await send_start_message(message)


@router2.message(F.text == "Админ-панель 🖥")
async def admin_panel(message: Message, state: FSMContext):
    if message.from_user.id == int(os.getenv("ADMIN_ID")):
        await state.set_state(Admin.admin_panel)
        await message.answer("Админ-панель активирована.", reply_markup=await admin_panel_buttons())
    else:
        await message.answer("⚠️ Номер введен некорректно.\n\n✅ Пример номера: <b>А123АА145</b>\n\n🔄 Попробуйте еще раз.")


@router2.message(Admin.admin_panel)
async def edit_json(message: Message, state: FSMContext):
    if message.text == "Файл логов":
        async with aiofiles.open("bot_logs.log", encoding="utf-8") as file:
            logs = await file.read()
            if logs:
                if len(logs) > 4000:
                    logs = logs[-4000:]
                await state.set_state(Admin.view_logs)
                await message.answer(logs, reply_markup=await clear_logs_button())
            else:
                await message.answer("Файл логов пуст", reply_markup=await admin_panel_buttons())
    elif message.text == "Состояние памяти":
        memory_info = get_memory_info()
        await message.answer(memory_info, reply_markup=await admin_panel_buttons())
    elif message.text == "Редактирование файла json":
        await state.set_state(Admin.editing_json)
        await message.answer("Выберите действие с файлом json.", reply_markup=await json_options_buttons())
    elif message.text == "Редактирование базы данных":
        await state.set_state(Admin.show_db)
        await message.answer("Выберите данные для вывода.", reply_markup=await choice_data_db_buttons())
    elif message.text == "Выйти из админ-панели":
        await state.clear()
        await message.answer("Вы успешно вышли из админ-панели.", reply_markup=ReplyKeyboardRemove())



@router2.message(Admin.editing_json)
async def back_to_menu(message: Message, state: FSMContext):
    if message.text == "Показать файл json" or message.text == "Добавить новое значение":
        async with aiofiles.open("database/models_for_drom.json", encoding="utf-8") as file:
            file_content = await file.read()
            json_data = json.loads(file_content)
        formatted_data = "\n".join(f"{i + 1} - {key}: {value}" for i, (key, value) in enumerate(json_data.items()))
        await message.answer(formatted_data, reply_markup=await add_value_json_button())

        if message.text == "Добавить новое значение":
            await state.set_state(Admin.adding_value_json)
            msg = "Напишите новое значение в формате: <b>&lt;id&gt; &lt;value&gt;</b>\nПример: <b>1 land_cruiser_prado</b>"
            await message.answer(msg, reply_markup=await finish_add_value_button())
    
    elif message.text == "Назад":
        await message.answer("Выберите действие с файлом json.", reply_markup=await json_options_buttons())
    
    elif message.text == "Вернуться в начальное меню":
        await state.set_state(Admin.admin_panel)
        await message.answer("Начальная панель", reply_markup=await admin_panel_buttons())



@router2.message(Admin.adding_value_json)
async def write_data_json(message: Message, state: FSMContext):
    if re.fullmatch("^(\d+)\s(.+)$", message.text):
        id, value = message.text.split()
        async with aiofiles.open("database/models_for_drom.json", "r+", encoding="utf-8") as file:
            file_content = await file.read()
            data = json.loads(file_content)
            try:
                key = list(data.keys())[int(id) - 1]
            except IndexError:
                await message.answer("Такого ID в файле нет.", reply_markup=await finish_add_value_button())
                return
            data[key] = value                               
            await file.seek(0)
            await file.write(json.dumps(data, ensure_ascii=False, indent=4))
            await file.truncate()

        await message.answer("Запись успешно добавлена.", reply_markup=await finish_add_value_button())
    elif message.text == "Завершить добавление значений":
        await state.set_state(Admin.editing_json)
        await message.answer("Добавление данных завершено.", reply_markup=await json_options_buttons())
    else:
        await message.answer("Неправильно введены данные.", reply_markup=await finish_add_value_button())



@router2.message(Admin.view_logs)
async def get_logs(message: Message, state: FSMContext):
    if message.text == "Очистить логи":
        async with aiofiles.open("bot_logs.log", "w"):
            pass
        await state.set_state(Admin.admin_panel)
        await message.answer("Логи очищены", reply_markup=await admin_panel_buttons())
    elif message.text == "Отправить файл логов":
        log_file = FSInputFile("bot_logs.log")
        await message.answer_document(log_file)
    elif message.text == "Вернуться в меню":
        await state.set_state(Admin.admin_panel)
        await message.answer("Вы вернулись в меню", reply_markup=await admin_panel_buttons())



@router2.message(Admin.show_db)
async def show_database(message: Message, state: FSMContext):
    query = None
    if message.text == "Номера":
        query = f"SELECT id, number FROM Carplates ORDER BY id"
    elif message.text == "Бренды":
        query = f"SELECT id, name FROM Brands ORDER BY id"
    elif message.text == "Модели":
        query = f"SELECT id, name FROM Models ORDER BY id"
    elif message.text == "Вернуться в начальное меню":
        await state.set_state(Admin.admin_panel)
        await message.answer("Возврат в меню", reply_markup=await admin_panel_buttons())
    if query:
        async with aiosqlite.connect("database/cars_database.db") as connection:
            cursor = await connection.cursor()
            await cursor.execute(query)
            result = await cursor.fetchall()
        formatted_data = "\n".join(f"{item[0]} - {item[1]}" for item in result)
        await state.set_state(Admin.editing_db)
        await message.answer(formatted_data, reply_markup=await del_data_db_buttons(message.text))


@router2.message(Admin.editing_db)
async def choice_data_for_del(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(Admin.show_db)
        await message.answer("Выберите данные для вывода.", reply_markup=await choice_data_db_buttons())
    else:
        await state.set_state(Admin.del_data_db)
        if message.text == "Удалить номер":
            await state.update_data(choice="Номер")
            await message.answer("Введите ID номера, для удаления", reply_markup=await back_button())
        elif message.text == "Удалить бренд":
            await state.update_data(choice="Бренд")
            await message.answer("Введите ID бренда, для удаления", reply_markup=await back_button())
        elif message.text == "Удалить модель":
            await state.update_data(choice="Модель")
            await message.answer("Введите ID модель, для удаления", reply_markup=await back_button())


@router2.message(Admin.del_data_db)
async def delete_data_db(message: Message, state: FSMContext):
    if message.text.isdigit():
        data = await state.get_data()
        choice_del = data["choice"]

        if choice_del == "Номер":
            query = "SELECT number FROM Carplates WHERE id=?"
        elif choice_del == "Бренд":
            query = "SELECT name FROM Brands WHERE id=?"
        elif choice_del == "Модель":
            query = "SELECT name FROM Models WHERE id=?"

        async with aiosqlite.connect("database/cars_database.db") as connection:
            cursor = await connection.cursor()
            await cursor.execute(query, (message.text,))
            element = await cursor.fetchone()
            if element:
                element = element[0]
                if choice_del == "Номер":
                    query = "DELETE FROM Carplates WHERE id=?"
                elif choice_del == "Бренд":
                    query = "DELETE FROM Brands WHERE id=?"
                elif choice_del == "Модель":
                    query = "DELETE FROM Models WHERE id=?"
                await cursor.execute(query, (message.text,))
                await connection.commit()
                await message.answer(f"{choice_del} '{element}' успешно удал{'ена' if choice_del == 'Модель' else 'ен'}.")
            else:
                await message.answer(f"{choice_del} с таким ID отсутствует.")

    elif message.text == "Назад":
        await state.set_state(Admin.show_db)
        await message.answer("Выберите данные для вывода.", reply_markup=await choice_data_db_buttons())
    else:
        await message.answer("Неправильно введены данные.", reply_markup=await back_button(), force_reply=True)
