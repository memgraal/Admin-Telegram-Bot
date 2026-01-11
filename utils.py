from functools import wraps
import logging

from aiogram import types
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


logger = logging.getLogger(__name__)


# Работает только в личном чате
def private_message(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type != ChatType.PRIVATE:
            return
        return await func(message, *args, **kwargs)

    return wrapper


# Получить юзернейм бота
async def get_bot_username():
    from bot import bot
    me = await bot.get_me()
    return me.username


# Безопасное удаление сообщения
async def delete_message_safe(message: types.Message):
    try:
        await message.delete()
        return True
    except TelegramForbiddenError:
        logger.error("❌ Нет прав на удаление сообщений")
    except TelegramBadRequest as e:
        logger.error(f"❌ Ошибка Telegram: {e}")
    return False
