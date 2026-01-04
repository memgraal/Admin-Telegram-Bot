from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


#
def bot_url_button(bot_username):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Перейти в бота", url=f"https://t.me/{bot_username}")
    )
    return builder.as_markup()