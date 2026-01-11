import asyncio
import logging

from aiogram import Bot, F, Router, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import utils
import database
import keyboards as kb
import constants as const


logger = logging.getLogger(__name__)
router_init_group = Router()


async def get_or_create_user(session: AsyncSession, tg_user_id: int):
    stmt = select(database.User).where(
        database.User.user_id == str(tg_user_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return user

    user = database.User(user_id=str(tg_user_id))
    session.add(user)
    await session.flush()
    return user


async def get_or_create_group(
    session: AsyncSession,
    chat_id: int,
    chat_title: str,
):
    stmt = select(database.Group).where(database.Group.chat_id == str(chat_id))
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if group:
        return group

    group = database.Group(
        chat_id=str(chat_id),
        settings=const.DEFAULT_GROUP_SETTINGS,
    )
    session.add(group)
    await session.flush()

    logger.info(f"Группа {chat_title} (ID: {chat_id}) добавлена в БД")
    return group


async def get_chat_admins_safely(bot: Bot, chat_id: int):
    admins = await bot.get_chat_administrators(chat_id)
    if admins:
        return admins

    # Telegram часто тупит после добавления бота
    await asyncio.sleep(1.0)
    return await bot.get_chat_administrators(chat_id)


@router_init_group.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
)
async def on_my_chat_member_update(
    update: types.ChatMemberUpdated,
    bot: Bot,
    session: AsyncSession,
):
    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status

    # Сработает только при добавлении/включении бота
    if (
        new_status not in const.MEMBER_OR_ADMINISTRATOR
        or old_status in const.MEMBER_OR_ADMINISTRATOR
    ):
        return

    chat_id = update.chat.id
    chat_title = update.chat.title

    group = await get_or_create_group(session, chat_id, chat_title)

    await asyncio.sleep(1.2)  # нужен для Telegram

    admins = await get_chat_admins_safely(bot, chat_id)
    logger.info(f"Админы группы {chat_title}: {admins}")

    for admin in admins:
        user = await get_or_create_user(session, admin.user.id)

        stmt = select(database.GroupUser).where(
            database.GroupUser.user_id == user.id,
            database.GroupUser.group_id == group.id,
        )
        result = await session.execute(stmt)
        group_user = result.scalar_one_or_none()

        if not group_user:
            session.add(
                database.GroupUser(
                    user_id=user.id,
                    group_id=group.id,
                    status=admin.status
                )
            )

    await session.commit()

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "Привет! Я бот-фильтр 👋\n"
            "Нажми кнопку ниже для доступа к настройкам:"
        ),
        reply_markup=kb.bot_url_button(await utils.get_bot_username()),
    )
