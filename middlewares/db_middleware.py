from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data) -> Any:
        async with self.session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
