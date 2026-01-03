from functools import wraps
from aiogram.enums import ChatType
from aiogram.types import Message

## Работает только в личном чате
def private_message(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type != ChatType.PRIVATE:
            return
        return await func(message, *args, **kwargs)
    return wrapper