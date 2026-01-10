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


@router_init_group.my_chat_member(
    F.chat.type.in_(
        {"group", "supergroup"},
    ),
)
async def on_my_chat_member_update(
    update: types.ChatMemberUpdated,
    bot: Bot,
    session: AsyncSession,
):

    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status

    if (
        new_status not in const.MEMBER_OR_ADMINISTRATOR
        or old_status in const.MEMBER_OR_ADMINISTRATOR
    ):
        return

    stmt = (
        select(database.Group)
        .where(
            database.Group.chat_id == str(
                update.chat.id
            )
        )
    )

    group = (
        await session
        .execute(stmt)
        .scalar_one_or_none()
    )

    if not group:
        group = database.Group(
            chat_id=str(update.chat.id),
            settings=const.DEFAULT_GROUP_SETTINGS,
        )

        session.add(group)
        await session.flush()

        logger.info(
            f"Группа {update.chat.title} "
            f"(ID: {update.chat.id}) добавлена в БД"
        )

    await asyncio.sleep(1.2)

    admins = await bot.get_chat_administrators(update.chat.id)

    logger.info(f"Админы группы {update.chat.title}: {admins}")

    if not admins:
        await asyncio.sleep(1.0)
        admins = await bot.get_chat_administrators(update.chat.id)

        logger.info(f"Повторный запрос админов: {admins}")

    for admin in admins:

        stmt = (
            select(database.User)
            .where(
                database.User.user_id == str(
                    admin.user.id,
                )
            )
        )

        user = (
            await session
            .execute(stmt)
            .scalar_one_or_none()
        )

        if not user:
            user = (
                database
                .User(
                    user_id=str(admin.user.id),
                )
            )
            session.add(user)
            await session.flush()

        stmt = (
            select(database.GroupUser)
            .where(
                database.GroupUser.user_id == user.id,
                database.GroupUser.group_id == group.id,
            )
        )

        group_user = (
            await session
            .execute(stmt)
            .scalar_one_or_none()
        )

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
        chat_id=update.chat.id,
        text=(
            "Привет! Я бот-фильтр 👋\n"
            "Нажми кнопку ниже для доступа к настройкам:"
        ),
        reply_markup=(
            kb
            .bot_url_button(
                await utils
                .get_bot_username()
            )
        ),
    )
