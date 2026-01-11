from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Group, GroupUser, User


class IsVerified(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession) -> bool:

        group = await session.scalar(
            select(Group).where(Group.chat_id == str(message.chat.id))
        )
        if not group:
            return False

        user = await session.scalar(
            select(User).where(User.user_id == str(message.from_user.id))
        )
        if not user:
            return False

        group_user = await session.scalar(
            select(GroupUser).where(
                GroupUser.group_id == group.id,
                GroupUser.user_id == user.id
            )
        )

        return bool(group_user and group_user.status == "member")
