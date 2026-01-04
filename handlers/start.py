import logging

from aiogram import Router, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import utils
import database
import keyboards


logger = logging.getLogger(__name__)

router_start = Router()


@router_start.message(CommandStart())
@utils.private_message
async def start(
    message: types.Message,
    state: FSMContext,
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
        reply_markup=await keyboards.groups_keyboard(
            groups=groups,
            page=0,
            bot=message.bot,
        )
    )


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
        reply_markup=await keyboards.groups_keyboard(
            groups=groups,
            page=page,
            bot=callback.bot,
        )
    )
    await callback.answer()


@router_start.callback_query(lambda c: c.data.startswith("group:"))
async def open_group(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    group_id = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.answer(f"⚙️ Настройки группы ID: {group_id}")
