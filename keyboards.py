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


def groups_keyboard(
    groups: list[database.Group],
    page: int,
) -> types.InlineKeyboardMarkup:

    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE
    current_groups = groups[start:end]

    builder = InlineKeyboardBuilder()

    for group in current_groups:
        title = getattr(group, "title", None) or f"ID {group.chat_id}"
        builder.button(
            text=f"📌 {title}",
            callback_data=f"group:{group.id}"
        )

    builder.adjust(1)

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


def group_settings_keyboard(
    group: database.Group
) -> types.InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()
    settings = group.settings or {}

    def toggle(key: str, title: str):
        value = settings.get(key, False)
        emoji = "✅" if value else "❌"
        builder.button(
            text=f"{emoji} {title}",
            callback_data=f"setting:{group.id}:{key}"
        )

    toggle("greeting", "Приветствие")
    toggle("captcha", "Капча")

    builder.adjust(1)

    builder.button(
        text="⬅️ Назад к группам",
        callback_data="back_to_groups"
    )

    return builder.as_markup()
