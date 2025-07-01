from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def admin_panel_buttons():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Файл логов")],
                                           [KeyboardButton(text="Состояние памяти")],
                                           [KeyboardButton(text="Редактирование файла json")],
                                           [KeyboardButton(text="Редактирование базы данных")],
                                           [KeyboardButton(text="Выйти из админ-панели")]],
                                 resize_keyboard=True)
    return markup


async def json_options_buttons():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Показать файл json")],
                                           [KeyboardButton(text="Добавить новое значение")],
                                           [KeyboardButton(text="Вернуться в начальное меню")]],
                                resize_keyboard=True)
    return markup


async def add_value_json_button():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Добавить новое значение")],
                                           [KeyboardButton(text="Назад")]],
                                resize_keyboard=True)
    return markup


async def finish_add_value_button():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Завершить добавление значений")]],
                                resize_keyboard=True)
    return markup


async def clear_logs_button():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Очистить логи")],
                                           [KeyboardButton(text="Отправить файл логов")],
                                           [KeyboardButton(text="Вернуться в меню")]],
                                resize_keyboard=True)
    return markup


async def choice_data_db_buttons():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Номера")],
                                           [KeyboardButton(text="Бренды")],
                                           [KeyboardButton(text="Модели")],
                                           [KeyboardButton(text="Вернуться в начальное меню")]],
                                 resize_keyboard=True)
    return markup


async def del_data_db_buttons(table: str):
    if table == "Номера":
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Удалить номер")],
                                               [KeyboardButton(text="Назад")]],
                                    resize_keyboard=True)
    elif table == "Бренды":
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Удалить бренд")],
                                               [KeyboardButton(text="Назад")]],
                                     resize_keyboard=True)
    elif table == "Модели":
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Удалить модель")],
                                               [KeyboardButton(text="Назад")]],
                                    resize_keyboard=True)
    return markup


async def back_button():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]],
                                 resize_keyboard=True)
    return markup