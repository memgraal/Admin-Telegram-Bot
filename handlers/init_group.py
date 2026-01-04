from aiogram import Router, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from utils import get_bot_username
import database
import keyboards as kb


logger = logging.getLogger(__name__)

router_init_group = Router()


@router_init_group.my_chat_member()
async def on_my_chat_member_update(
    update: types.ChatMemberUpdated,
    session: AsyncSession,
):
    if update.chat.type not in ("group", "supergroup"):
        return

    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status

    # бот только что был добавлен
    if new_status not in ("member", "administrator"):
        return

    if old_status in ("member", "administrator"):
        return  # уже был в группе

    stmt = select(database.Group).where(
        database.Group.chat_id == str(update.chat.id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        group = database.Group(
            chat_id=str(update.chat.id),
            settings={
                "greeting": True,
                "captcha": True,
                "banwords": []
            }
        )
        session.add(group)
        await session.commit()

        logger.info(
            f"Группа {update.chat.title} (ID: {update.chat.id}) добавлена в БД"
        )

    await update.bot.send_message(
        chat_id=update.chat.id,
        text="Привет! Я бот-фильтр 👋\n"
             "Нажми кнопку ниже для доступа к настройкам:",
        reply_markup=kb.bot_url_button(await get_bot_username()),
    )
