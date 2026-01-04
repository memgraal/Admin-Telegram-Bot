from aiogram import Router, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
import logging

import utils

logger = logging.getLogger(__name__)

router_start = Router()


@router_start.message(CommandStart())
@utils.private_message
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "Здесь <b>будет</b> список ваших групп.", parse_mode=ParseMode.HTML
    )
