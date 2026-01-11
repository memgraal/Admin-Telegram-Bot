from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import database


async def is_message_in_ban(
    text: str,
    session: AsyncSession,
    chat_id: str,
) -> bool:

    settings = await session.scalar(
        select(database.Group.settings)
        .where(database.Group.chat_id == chat_id)
    )

    if not settings:
        return

    banwords = settings.get("banwords", [])
    if not banwords:
        return

    text = text.lower()

    return any(word in text for word in banwords)
