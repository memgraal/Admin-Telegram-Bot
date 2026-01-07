import asyncio
import logging
from typing import Dict, Tuple

from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ⬇️ ИМПОРТ СВОИХ МОДЕЛЕЙ (ПРОВЕРЬ ПУТЬ!)
from database import Group, GroupUser, User, Logs
from filters.is_not_verified import IsNotVerified


logger = logging.getLogger(__name__)

router_captcha = Router()

# (chat_id, user_id) -> data
pending_captcha: Dict[Tuple[int, int], dict] = {}
CAPTCHA_TIMEOUT = 30  # ⬅️ МОЖЕШЬ ПОМЕНЯТЬ


# =========================
# Keyboard
# =========================
def captcha_keyboard(chat_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Я не бот",
                    callback_data=f"captcha:{chat_id}:{user_id}"
                )
            ]
        ]
    )


# =========================
# MESSAGE HANDLER
# =========================
@router_captcha.message(
    F.chat.type.in_(("group", "supergroup")),
    IsNotVerified()
)
async def captcha_message_handler(
    message: types.Message,
    session: AsyncSession
):
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    key = (chat_id, user_id)

    # =========================
    # 1️⃣ Получаем группу
    # =========================
    group = await session.scalar(
        select(Group).where(Group.chat_id == str(chat_id))
    )
    if not group:
        return

    # =========================
    # 2️⃣ Проверяем, включена ли капча
    # ⚠️ ВАЖНО: ключ "captcha"
    # =========================
    if not group.settings.get("captcha", False):
        return

    # =========================
    # 3️⃣ Получаем / создаём User
    # =========================
    user = await session.scalar(
        select(User).where(User.user_id == str(user_id))
    )
    if not user:
        user = User(user_id=str(user_id))
        session.add(user)
        await session.commit()

    # =========================
    # 4️⃣ Проверяем GroupUser
    # =========================
    group_user = await session.scalar(
        select(GroupUser).where(
            GroupUser.user_id == user.id,
            GroupUser.group_id == group.id
        )
    )

    # Если уже подтверждён → ничего не делаем
    if group_user and group_user.status == "member":
        return

    # =========================
    # 5️⃣ Если капча уже показана
    # =========================
    if key in pending_captcha:
        try:
            await message.delete()
        except TelegramForbiddenError:
            pass
        return

    # =========================
    # 6️⃣ Если записи нет — создаём pending
    # =========================
    if not group_user:
        group_user = GroupUser(
            user_id=user.id,
            group_id=group.id,
            status="pending"  # ⬅️ ВАЖНО
        )
        session.add(group_user)
        await session.commit()

    # =========================
    # 7️⃣ Удаляем сообщение
    # =========================
    try:
        await message.delete()
    except TelegramForbiddenError:
        pass

    # =========================
    # 8️⃣ Отправляем капчу
    # =========================
    captcha_msg = await message.answer(
        f"👋 {message.from_user.mention_html()}, подтвердите, что вы не бот\n"
        f"⏳ У вас {CAPTCHA_TIMEOUT} секунд",
        reply_markup=captcha_keyboard(chat_id, user_id),
        parse_mode="HTML"
    )

    async def timeout():
        await asyncio.sleep(CAPTCHA_TIMEOUT)
        pending_captcha.pop(key, None)

        try:
            await captcha_msg.delete()
        except TelegramBadRequest:
            pass

        session.add(
            Logs(
                chat_id=str(chat_id),
                user_id=str(user_id),
                action="captcha_timeout"
            )
        )
        await session.commit()

    task = asyncio.create_task(timeout())

    pending_captcha[key] = {
        "task": task,
        "group_user_id": group_user.id
    }


# =========================
# CALLBACK HANDLER
# =========================
@router_captcha.callback_query(F.data.startswith("captcha:"))
async def captcha_confirm(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    _, chat_id, user_id = callback.data.split(":")
    chat_id = int(chat_id)
    user_id = int(user_id)

    if callback.from_user.id != user_id:
        await callback.answer("❌ Это не для вас", show_alert=True)
        return

    key = (chat_id, user_id)
    data = pending_captcha.pop(key, None)

    if not data:
        await callback.answer("⏳ Время вышло", show_alert=True)
        return

    data["task"].cancel()

    # =========================
    # 9️⃣ Обновляем статус
    # =========================
    group_user = await session.get(GroupUser, data["group_user_id"])
    if group_user:
        group_user.status = "member"

    session.add(
        Logs(
            chat_id=str(chat_id),
            user_id=str(user_id),
            action="captcha_passed"
        )
    )
    await session.commit()

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await callback.answer("✅ Спасибо! Теперь вы можете писать")
