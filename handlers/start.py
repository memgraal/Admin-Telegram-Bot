import logging

from aiogram import Router, types
from aiogram.filters.command import CommandStart
from aiogram.enums import ParseMode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import utils
import database
import keyboards


logger = logging.getLogger(__name__)

router_start = Router()


# =========================
# /start — список групп
# =========================
@router_start.message(CommandStart())
@utils.private_message
async def start(
    message: types.Message,
    session: AsyncSession
) -> None:

    user_id = str(message.from_user.id)

    stmt = (
        select(database.Group)
        .join(database.GroupUser)
        .join(database.User)
        .where(
            database.User.user_id == user_id,
            database.GroupUser.status.in_(("administrator", "creator"))
        )
        .order_by(database.Group.id)
    )

    result = await session.execute(stmt)
    groups = result.scalars().all()

    if not groups:
        await message.answer(
            "❌ У вас нет групп, где вы администратор",
            parse_mode=ParseMode.HTML
        )
        return

    await message.answer(
        "<b>📋 Список ваших групп (админ):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.groups_keyboard(groups, page=0)
    )


# =========================
# Пагинация групп
# =========================
@router_start.callback_query(lambda c: c.data.startswith("groups_page:"))
async def paginate_groups(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    page = int(callback.data.split(":")[1])
    user_id = str(callback.from_user.id)

    stmt = (
        select(database.Group)
        .join(database.GroupUser)
        .join(database.User)
        .where(
            database.User.user_id == user_id,
            database.GroupUser.status.in_(("administrator", "creator"))
        )
        .order_by(database.Group.id)
    )

    result = await session.execute(stmt)
    groups = result.scalars().all()

    await callback.message.edit_reply_markup(
        reply_markup=keyboards.groups_keyboard(groups, page)
    )
    await callback.answer()


# =========================
# Открыть настройки группы
# =========================
@router_start.callback_query(lambda c: c.data.startswith("group:"))
async def open_group(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    group_id = int(callback.data.split(":")[1])

    stmt = select(database.Group).where(database.Group.id == group_id)
    result = await session.execute(stmt)
    group = result.scalar_one()

    await callback.message.edit_text(
        "<b>⚙️ Настройки группы</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.group_settings_keyboard(group)
    )
    await callback.answer()


# =========================
# Toggle настройки (True ⇄ False)
# =========================
@router_start.callback_query(lambda c: c.data.startswith("setting:"))
async def toggle_setting(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    _, group_id, key = callback.data.split(":")
    group_id = int(group_id)

    stmt = select(database.Group).where(database.Group.id == group_id)
    result = await session.execute(stmt)
    group = result.scalar_one()

    settings = group.settings or {}
    settings[key] = not settings.get(key, False)
    group.settings = settings

    await session.commit()

    await callback.message.edit_reply_markup(
        reply_markup=keyboards.group_settings_keyboard(group)
    )
    await callback.answer("Настройка обновлена")


# =========================
# Назад к списку групп
# =========================
@router_start.callback_query(lambda c: c.data == "back_to_groups")
async def back_to_groups(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    user_id = str(callback.from_user.id)

    stmt = (
        select(database.Group)
        .join(database.GroupUser)
        .join(database.User)
        .where(
            database.User.user_id == user_id,
            database.GroupUser.status.in_(("administrator", "creator"))
        )
        .order_by(database.Group.id)
    )

    result = await session.execute(stmt)
    groups = result.scalars().all()

    await callback.message.edit_text(
        "<b>📋 Список ваших групп (админ):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.groups_keyboard(groups, page=0)
    )
    await callback.answer()
