import logging

from aiogram import Router, types, Bot
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import utils
import database
import keyboards
from states import AddBanWords

logger = logging.getLogger(__name__)

router_start = Router()


# =========================
# helper: sync admins for group
# =========================
async def sync_group_admins(
    group: database.Group, bot: Bot, session: AsyncSession
):
    try:
        admins = await bot.get_chat_administrators(int(group.chat_id))
    except Exception as e:
        logger.warning(
            f"Не удалось получить админов группы {group.chat_id}: {e}"
        )
        return

    for admin in admins:
        tg_user = admin.user
        status = admin.status  # creator | administrator

        # --- User ---
        stmt = (
            select(database.User)
            .where(database.User.user_id == str(tg_user.id))
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = database.User(user_id=str(tg_user.id))
            session.add(user)
            await session.flush()

        # --- GroupUser ---
        stmt = select(database.GroupUser).where(
            database.GroupUser.user_id == user.id,
            database.GroupUser.group_id == group.id
        )
        result = await session.execute(stmt)
        gu = result.scalar_one_or_none()

        if not gu:
            session.add(
                database.GroupUser(
                    user_id=user.id,
                    group_id=group.id,
                    status=status
                )
            )

    await session.commit()


# =========================
# /start — список групп
# =========================
@router_start.message(CommandStart())
@utils.private_message
async def start(
    message: types.Message,
    session: AsyncSession,
    bot: Bot
) -> None:
    user_id = str(message.from_user.id)

    stmt = select(database.Group)
    groups_all = (await session.execute(stmt)).scalars().all()

    for group in groups_all:
        await sync_group_admins(group, bot, session)

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

    groups = (await session.execute(stmt)).scalars().all()

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

    groups = (await session.execute(stmt)).scalars().all()

    await callback.message.edit_reply_markup(
        reply_markup=keyboards.groups_keyboard(groups, page)
    )
    await callback.answer()


@router_start.callback_query(lambda c: c.data.startswith("group:"))
async def open_group(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    group_id = int(callback.data.split(":")[1])

    group = await session.scalar(
        select(database.Group).where(database.Group.id == group_id)
    )

    await callback.message.edit_text(
        "<b>⚙️ Настройки группы</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.group_settings_keyboard(group)
    )
    await callback.answer()


@router_start.callback_query(lambda c: c.data.startswith("setting:"))
async def toggle_setting(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    _, group_id, key = callback.data.split(":")
    group_id = int(group_id)

    group = await session.scalar(
        select(database.Group).where(database.Group.id == group_id)
    )

    settings = group.settings or {}
    settings[key] = not settings.get(key, False)
    group.settings = settings

    await callback.message.edit_reply_markup(
        reply_markup=keyboards.group_settings_keyboard(group)
    )
    await callback.answer("Настройка обновлена")


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

    groups = (await session.execute(stmt)).scalars().all()

    await callback.message.edit_text(
        "<b>📋 Список ваших групп (админ):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.groups_keyboard(groups, page=0)
    )
    await callback.answer()


@router_start.callback_query(lambda c: c.data.startswith("add_banwords:"))
async def ask_banwords(
    callback: types.CallbackQuery,
    state: FSMContext
):
    group_id = int(callback.data.split(":")[1])

    await state.set_state(AddBanWords.waiting_for_words)
    await state.update_data(group_id=group_id)

    await callback.message.answer(
        "✍️ Отправьте бан-слова через пробел или с новой строки\n\n"
        "<i>Пример:</i>\nпизда казино реклама",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router_start.message(AddBanWords.waiting_for_words)
async def save_banwords(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext
):
    text = message.text.strip().lower()

    data = await state.get_data()
    group_id = data["group_id"]

    group = await session.scalar(
        select(database.Group).where(database.Group.id == group_id)
    )

    if not group:
        await message.answer("❌ Группа не найдена")
        await state.clear()
        return

    settings = group.settings or {}
    banwords = {
        w for w in settings.get("banwords", [])
        if w and w.strip()
    }

    if text == "show":
        if not banwords:
            await message.answer("📭 Список бан-слов пуст")
        else:
            await message.answer(
                "🚫 <b>Бан-слова:</b>\n\n"
                f"<code>{', '.join(sorted(banwords))}</code>",
                parse_mode=ParseMode.HTML
            )
        await state.clear()
        return

    if text in {"delete", "del", "clear"}:
        settings["banwords"] = []
        group.settings = settings

        await message.answer(
            "🗑 Все бан-слова удалены",
            parse_mode=ParseMode.HTML
        )
        await state.clear()
        return

    # ADD
    words = {
        w.strip().lower()
        for w in message.text.replace("\n", " ").split(" ")
        if w.strip()
    }

    if not words:
        await message.answer("❌ Список пуст")
        return

    banwords.update(words)
    settings["banwords"] = sorted(banwords)
    group.settings = settings

    await message.answer(
        f"✅ Добавлено слов: <b>{len(words)}</b>\n\n"
        f"<code>{', '.join(settings['banwords'])}</code>",
        parse_mode=ParseMode.HTML
    )

    await state.clear()
