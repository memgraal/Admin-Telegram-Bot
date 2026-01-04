from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database


GROUPS_PER_PAGE = 5


def bot_url_button(bot_username: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Перейти в бота",
        url=f"https://t.me/{bot_username}"
    )
    return builder.as_markup()


async def groups_keyboard(
    groups: list[database.Group],
    page: int,
    bot,
) -> types.InlineKeyboardMarkup:

    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE
    current_groups = groups[start:end]

    builder = InlineKeyboardBuilder()

    # кнопки групп
    for group in current_groups:
        chat = await bot.get_chat(int(group.chat_id))
        title = chat.title or group.chat_id

        builder.button(
            text=f"📌 {title}",
            callback_data=f"group:{group.id}"
        )

    # каждая группа — отдельная строка
    builder.adjust(1)

    # навигация
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"groups_page:{page - 1}"
            )
        )

    if end < len(groups):
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="➡️ Вперёд",
                callback_data=f"groups_page:{page + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()
