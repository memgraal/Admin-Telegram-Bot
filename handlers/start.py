import logging

from aiogram import Router, types
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

    groups = (await session.execute(stmt)).scalars().all()

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

    group = await session.scalar(
        select(database.Group).where(database.Group.id == group_id)
    )

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

    groups = (await session.execute(stmt)).scalars().all()

    await callback.message.edit_text(
        "<b>📋 Список ваших групп (админ):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.groups_keyboard(groups, page=0)
    )
    await callback.answer()


# =========================
# Добавление banwords — старт
# =========================
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


# =========================
# Добавление banwords — сохранение
# =========================
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

    # =========================
    # SHOW
    # =========================
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

    # =========================
    # DELETE / DEL / CLEAR
    # =========================
    if text in {"delete", "del", "clear"}:
        settings["banwords"] = []
        group.settings = settings

        await message.answer(
            "🗑 Все бан-слова удалены",
            parse_mode=ParseMode.HTML
        )
        await state.clear()
        return

    # =========================
    # ADD WORDS
    # =========================
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
