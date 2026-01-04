from aiogram import Router, F, types, Dispatcher
from aiogram.filters.command import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
import logging

from aiogram.types import InlineKeyboardMarkup

import database as db
from utils import *
import keyboards as kb

logger = logging.getLogger(__name__)

router_init_group = Router()


async def on_chat_member_update(update: types.ChatMemberUpdated, dp: Dispatcher):
    # update.chat.type == 'group' or 'supergroup'
    if update.new_chat_member.is_bot and update.new_chat_member.status in ['member', 'administrator']:
        # Бот добавлен в группу (или его роль изменилась)

        logger.info(f"Бот {update.new_chat_member.username} добавлен в группу {update.chat.title}")
        await update.bot.send_message(update.chat.id, f"Привет! Я бот фильтр! Нажми тут для доступа к настройкам:", reply_markup=kb.bot_url_button(await get_bot_username()))