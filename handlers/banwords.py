import logging

from aiogram import Router, types, F
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from database import Group
from filters.is_verified import IsVerified  # ⬅️ ВАЖНО

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

    chat_id = str(message.chat.id)

    settings = await session.scalar(
        select(Group.settings).where(Group.chat_id == chat_id)
    )
    if not settings:
        return

    banwords = settings.get("banwords", [])
    if not banwords:
        return

    text = text.lower()

    if any(word in text for word in banwords):
        try:
            await message.delete()
            logger.warning(
                f"🛑 Banword deleted in chat {chat_id}: {text}"
            )
        except TelegramForbiddenError:
            logger.error("❌ Нет прав на удаление сообщений")
        except TelegramBadRequest as e:
            logger.error(f"❌ Ошибка Telegram: {e}")
