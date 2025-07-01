from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


async def description_button():
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Описание машины 📝", callback_data="description")]])
    return markup


async def admin_button():
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Админ-панель 🖥")]],
                                 resize_keyboard=True)
    return markup
