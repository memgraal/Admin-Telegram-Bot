import logging

from aiogram import Router, types, F
from aiogram.types import ChatMemberOwner, ChatMemberAdministrator
from sqlalchemy.ext.asyncio import AsyncSession

from filters.is_verified import IsVerified
from filters.banned_text import is_message_in_ban
import utils

logger = logging.getLogger(__name__)

router_banwords = Router()


@router_banwords.message(
    F.chat.type.in_(("group", "supergroup")),
    IsVerified()
)
async def banwords_handler(
    message: types.Message,
    session: AsyncSession
):
    text = message.text or message.caption
    if not text:
        return

    # ❌ не трогаем посты канала
    if message.is_automatic_forward:
        return

    # ❌ не трогаем сообщения от каналов / анонимных админов
    if message.sender_chat is not None:
        return

    if message.from_user is None:
        return

    member = await message.bot.get_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
    )

    # 🔒 админы и создатель
    if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator)):
        return

    if not await is_message_in_ban(
        text=text,
        session=session,
        chat_id=str(message.chat.id),
    ):
        return

    await utils.delete_message_safe(message)
