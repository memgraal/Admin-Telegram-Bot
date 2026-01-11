import logging

from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession

from filters.is_verified import IsVerified
from filters.banned_text import is_message_in_ban
import utils

logger = logging.getLogger(__name__)

router_banwords = Router()


@router_banwords.message(
    F.chat.type.in_(("group", "supergroup")), IsVerified()
)
async def banwords_handler(
    message: types.Message,
    session: AsyncSession
):
    text = message.text or message.caption
    if not text:
        return

    if not await is_message_in_ban(
        text=text,
        session=session,
        chat_id=str(message.chat.id),
    ):
        return

    await utils.delete_message_safe(message)
