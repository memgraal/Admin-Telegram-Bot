from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Group  # путь подставь свой


class BanWordsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: Dict[str, Any]
    ):
        if event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        if not event.text:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        chat_id = str(event.chat.id)  # 🔥 ВАЖНО

        settings = await session.scalar(
            select(Group.settings).where(Group.chat_id == chat_id)
        )

        if not settings:
            return await handler(event, data)

        banwords = settings.get("banwords", [])
        if not banwords:
            return await handler(event, data)

        text = event.text.lower()

        if any(word in text for word in banwords):
            await event.delete()
            return  # ⛔ дальше НИЧЕГО не идёт

        return await handler(event, data)
