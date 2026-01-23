from functools import wraps
import logging

from aiogram import types, Bot
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

logger = logging.getLogger(__name__)


# =========================
# Работает только в личке
# =========================
def private_message(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type != ChatType.PRIVATE:
            print(
                f"[private_message] ignored "
                f"chat_type={message.chat.type}"
            )
            return
        return await func(message, *args, **kwargs)

    return wrapper


# =========================
# Получить юзернейм бота
# =========================
_bot_username_cache: str | None = None


async def get_bot_username(bot: Bot) -> str:
    global _bot_username_cache

    if _bot_username_cache:
        return _bot_username_cache

    me = await bot.get_me()
    _bot_username_cache = me.username

    print(f"[get_bot_username] cached username={_bot_username_cache}")
    return _bot_username_cache


# =========================
# Безопасное удаление сообщения
# =========================
async def delete_message_safe(message: types.Message) -> bool:
    try:
        await message.delete()
        return True

    except TelegramForbiddenError:
        logger.error(
            f"❌ Нет прав на удаление сообщения "
            f"chat_id={message.chat.id} "
            f"msg_id={message.message_id}"
        )

    except TelegramBadRequest as e:
        logger.error(
            f"❌ Ошибка Telegram при удалении "
            f"chat_id={message.chat.id} "
            f"msg_id={message.message_id}: {e}"
        )

    return False
