from aiogram.filters import Filter
from aiogram.types import Message


class IsHuman(Filter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.sender_chat is None
            and not message.from_user.is_bot
        )
