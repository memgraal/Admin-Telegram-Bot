import asyncio
import logging
from typing import Dict, Tuple

from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
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

# (chat_id, user_id) -> data
pending_captcha: Dict[Tuple[int, int], dict] = {}
CAPTCHA_TIMEOUT = 30


@router_captcha.message(
    F.chat.type.in_(("group", "supergroup")),
    IsNotVerified(),
    IsHuman()
)
async def captcha_message_handler(
    message: types.Message,
    session: AsyncSession,
):
    if message.from_user.is_bot:
        return

    # ❌ не трогаем посты канала
    if message.is_automatic_forward:
        return

    # ❌ не трогаем сообщения от каналов / анонимных админов
    if message.sender_chat is not None:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    key = (chat_id, user_id)

    text = message.text or message.caption
    if text and await is_message_in_ban(
        text=text,
        session=session,
        chat_id=str(chat_id),
    ):
        await utils.delete_message_safe(message)
        return

    group = await session.scalar(
        select(Group)
        .where(
            Group.chat_id == str(chat_id)
        )
    )
    if not group:
        return

    if not group.settings.get("captcha", False):
        return

    user = await session.scalar(
        select(User)
        .where(
            User.user_id == str(user_id)
        )
    )
    if not user:
        user = User(user_id=str(user_id))
        session.add(user)
        await session.commit()

    group_user = await session.scalar(select(GroupUser).where(
        GroupUser.user_id == user.id,
        GroupUser.group_id == group.id
    ))

    if group_user and group_user.status == "member":
        return

    if key in pending_captcha:
        try:
            await message.delete()
        except TelegramForbiddenError:
            pass
        return

    if not group_user:
        group_user = GroupUser(
            user_id=user.id,
            group_id=group.id,
            status="pending"
        )
        session.add(group_user)
        await session.commit()

    try:
        captcha_msg = await message.reply(
            f"👋 {message.from_user.mention_html()}, "
            "подтвердите, что вы не бот\n"
            f"⏳ У вас {CAPTCHA_TIMEOUT} секунд",
            reply_markup=captcha_keyboard(chat_id, user_id),
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        captcha_msg = await message.bot.send_message(
            chat_id=chat_id,
            text=(
                f"👋 {message.from_user.mention_html()}, "
                "подтвердите, что вы не бот\n"
                f"⏳ У вас {CAPTCHA_TIMEOUT} секунд"
            ),
            reply_markup=captcha_keyboard(chat_id, user_id),
            parse_mode="HTML"
        )

    async def timeout():
        await asyncio.sleep(CAPTCHA_TIMEOUT)

        data = pending_captcha.pop(key, None)
        if not data:
            return

        try:
            await captcha_msg.delete()
        except TelegramBadRequest:
            pass

        try:
            await message.delete()
        except TelegramBadRequest:
            pass

        session.add(Logs(
            chat_id=str(chat_id),
            user_id=str(user_id),
            action="captcha_timeout"
        ))
        await session.commit()

    task = asyncio.create_task(timeout())

    pending_captcha[key] = {
        "task": task,
        "captcha_msg_id": captcha_msg.message_id,
        "user_msg_id": message.message_id,
        "group_user_id": group_user.id
    }


@router_captcha.callback_query(F.data.startswith("captcha:"))
async def captcha_confirm(
    callback: types.CallbackQuery,
    session: AsyncSession,
):
    _, chat_id, user_id = callback.data.split(":")
    chat_id = int(chat_id)
    user_id = int(user_id)

    # не тот пользователь
    if callback.from_user.id != user_id:
        await callback.answer("❌ Это не для вас", show_alert=True)
        return

    key = (chat_id, user_id)
    data = pending_captcha.pop(key, None)

    if not data:
        await callback.answer("⏳ Время вышло", show_alert=True)
        return

    data["task"].cancel()

    # обновляем статус
    group_user = await session.get(GroupUser, data["group_user_id"])
    if group_user:
        group_user.status = "member"

    session.add(Logs(
        chat_id=str(chat_id),
        user_id=str(user_id),
        action="captcha_passed"
    ))
    await session.commit()

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await callback.answer("✅ Спасибо! Теперь вы можете писать")
