import asyncio
import logging
from typing import Dict, Tuple

from aiogram import Router, types, F
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import utils
from keyboards import captcha_keyboard
from database import Group, GroupUser, User, Logs
from filters.is_not_verified import IsNotVerified
from filters.banned_text import is_message_in_ban
from filters.is_human import IsHuman

logger = logging.getLogger(__name__)
router_captcha = Router()

# (chat_id, user_id) -> task
pending_captcha: Dict[Tuple[int, int], asyncio.Task] = {}
CAPTCHA_TIMEOUT = 30


@router_captcha.message(
    F.chat.type.in_(("group", "supergroup")),
    IsNotVerified(),
    IsHuman(),
)
async def captcha_message_handler(
    message: types.Message,
    session: AsyncSession,
):

    if (
        message.new_chat_members
        or message.left_chat_member
        or message.new_chat_title
        or message.new_chat_photo
        or message.delete_chat_photo
        or message.group_chat_created
        or message.supergroup_chat_created
        or message.channel_chat_created
        or message.pinned_message
    ):
        return

    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    key = (chat_id, user_id)

    member = await message.bot.get_chat_member(chat_id, user_id)
    if member.status in ("administrator", "creator"):
        return

    text = message.text or message.caption
    if text and await is_message_in_ban(
        text=text,
        session=session,
        chat_id=str(chat_id),
    ):
        await utils.delete_message_safe(message)
        return

    group = await session.scalar(
        select(Group).where(Group.chat_id == str(chat_id))
    )
    if not group or not group.settings.get("captcha", False):
        return

    user = await session.scalar(
        select(User).where(User.user_id == str(user_id))
    )
    if not user:
        user = User(user_id=str(user_id))
        session.add(user)
        await session.commit()

    gu = await session.scalar(
        select(GroupUser).where(
            GroupUser.user_id == user.id,
            GroupUser.group_id == group.id,
        )
    )

    if gu and gu.status == "member":
        return

    if key in pending_captcha:
        await utils.delete_message_safe(message)
        return

    if not gu:
        gu = GroupUser(
            user_id=user.id,
            group_id=group.id,
            status="pending",
        )
        session.add(gu)
        await session.commit()

    captcha_msg = await message.reply(
        f"👋 {message.from_user.mention_html()}, подтвердите, что вы не бот\n"
        f"⏳ У вас {CAPTCHA_TIMEOUT} секунд",
        reply_markup=captcha_keyboard(chat_id, user_id),
        parse_mode="HTML",
    )

    async def timeout():
        try:
            await asyncio.sleep(CAPTCHA_TIMEOUT)
        except asyncio.CancelledError:
            return

        pending_captcha.pop(key, None)

        await utils.delete_message_safe(captcha_msg)
        await utils.delete_message_safe(message)

    pending_captcha[key] = asyncio.create_task(timeout())


@router_captcha.callback_query(F.data.startswith("captcha:"))
async def captcha_confirm(
    callback: types.CallbackQuery,
    session: AsyncSession,
):
    _, chat_id, user_id = callback.data.split(":")
    chat_id = int(chat_id)
    user_id = int(user_id)

    if callback.from_user.id != user_id:
        await callback.answer("❌ Это не для вас", show_alert=True)
        return

    key = (chat_id, user_id)
    task = pending_captcha.pop(key, None)
    if task:
        task.cancel()

    gu = await session.scalar(
        select(GroupUser)
        .join(Group)
        .where(
            Group.chat_id == str(chat_id),
            GroupUser.user.has(user_id=str(user_id)),
        )
    )

    if gu:
        gu.status = "member"

    session.add(
        Logs(
            chat_id=str(chat_id),
            user_id=str(user_id),
            action="captcha_passed",
        )
    )
    await session.commit()

    await utils.delete_message_safe(callback.message)
    await callback.answer("✅ Спасибо! Теперь вы можете писать")
