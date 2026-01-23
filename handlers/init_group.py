import logging

from aiogram import Bot, F, Router, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import database
import keyboards as kb
import utils

logger = logging.getLogger(__name__)
router_init_group = Router()


# =========================
# helpers
# =========================
async def get_or_create_user(session: AsyncSession, tg_user_id: int):
    stmt = select(database.User).where(
        database.User.user_id == str(tg_user_id)
    )
    user = (await session.execute(stmt)).scalar_one_or_none()

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
    stmt = select(database.Group).where(
        database.Group.chat_id == str(chat_id)
    )
    group = (await session.execute(stmt)).scalar_one_or_none()

    if group:
        return group

    group = database.Group(
        chat_id=str(chat_id),
        settings={},
    )
    session.add(group)
    await session.flush()

    logger.info(f"Группа добавлена: {chat_title}")
    return group


# =========================
# bot became admin
# =========================
@router_init_group.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.new_chat_member.user.is_bot,
)
async def on_bot_became_admin(
    event: types.ChatMemberUpdated,
    bot: Bot,
    session: AsyncSession,
):
    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status

    print(
        f"[on_bot_became_admin] chat_id={event.chat.id} "
        f"old={old_status} new={new_status}"
    )

    # ❗ реагируем ТОЛЬКО когда бот стал админом
    if new_status not in ("administrator", "creator"):
        return

    group = await get_or_create_group(
        session,
        event.chat.id,
        event.chat.title
    )

    admins = await bot.get_chat_administrators(event.chat.id)
    print(f"[on_bot_became_admin] admins count={len(admins)}")

    for admin in admins:
        user = await get_or_create_user(session, admin.user.id)

        gu = await session.scalar(
            select(database.GroupUser).where(
                database.GroupUser.user_id == user.id,
                database.GroupUser.group_id == group.id,
            )
        )

        if not gu:
            session.add(
                database.GroupUser(
                    user_id=user.id,
                    group_id=group.id,
                    status=admin.status
                )
            )
            print(
                f"[on_bot_became_admin] ADD admin "
                f"user_id={user.id} status={admin.status}"
            )
        else:
            gu.status = admin.status

    await session.commit()
    print("[on_bot_became_admin] admins synced")

    await bot.send_message(
        chat_id=event.chat.id,
        text=(
            "Привет! Я бот-фильтр 👋\n"
            "Нажми кнопку ниже для доступа к настройкам:"
        ),
        reply_markup=kb.bot_url_button(
            await utils.get_bot_username(bot)
        ),
    )


# =========================
# admin added / changed
# =========================
@router_init_group.chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    ~F.new_chat_member.user.is_bot,
)
async def on_admin_update(
    event: types.ChatMemberUpdated,
    session: AsyncSession,
):
    new_status = event.new_chat_member.status

    if new_status not in ("administrator", "creator"):
        return

    user = await get_or_create_user(
        session,
        event.new_chat_member.user.id
    )
    group = await get_or_create_group(
        session,
        event.chat.id,
        event.chat.title
    )

    gu = await session.scalar(
        select(database.GroupUser).where(
            database.GroupUser.user_id == user.id,
            database.GroupUser.group_id == group.id,
        )
    )

    if not gu:
        session.add(
            database.GroupUser(
                user_id=user.id,
                group_id=group.id,
                status=new_status
            )
        )
    else:
        gu.status = new_status

    await session.commit()
