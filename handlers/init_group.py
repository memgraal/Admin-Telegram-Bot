from aiogram import Router, types, Dispatcher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging


from utils import get_bot_username
import database
import keyboards as kb

logger = logging.getLogger(__name__)

router_init_group = Router()


async def on_chat_member_update(
    update: types.ChatMemberUpdated, dp: Dispatcher,  session: AsyncSession
):
    # update.chat.type == 'group' or 'supergroup'
    if update.new_chat_member.is_bot and update.new_chat_member.status in [
        "member",
        "administrator",
    ]:
        # Бот добавлен в группу (или его роль изменилась)
        stmt = select(database.Group).where(
            database.Group.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()
        if not group:
            new_group = database.Group(
                chat_id=str(update.chat.id),
                # Задаем начальные настройки (как мы обсуждали ранее)
                settings={
                    "greeting": True,
                    "captcha": True,
                    "banwords": []
                }
            )
            session.add(new_group)
            await session.commit()

            logger.info(
                f"Группа {update.chat.title} (ID: {str(update.chat.id)})"
                " добавлена в базу.",
                )
        else:
            logger.info(f"Группа {update.chat.title} уже есть в базе.")

        logger.info(
            f"Бот {update.new_chat_member.username} "
            f"добавлен в группу {update.chat.title}"
        )
        await update.bot.send_message(
            update.chat.id,
            "Привет! Я бот фильтр! Нажми тут для доступа к настройкам:",
            reply_markup=kb.bot_url_button(await get_bot_username()),
        )
