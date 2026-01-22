import re

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
        return False

    banwords = settings.get("banwords", [])
    if not banwords:
        return False

    text = text.lower()

    for word in banwords:
        pattern = rf"\b{re.escape(word.lower())}\b"
        if re.search(pattern, text):
            return True

    return False
