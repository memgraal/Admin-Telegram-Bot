from aiogram import Router, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
import logging

import database as db
from utils import *

logger = logging.getLogger(__name__)

router_start = Router()


@router_start.message(Command("start"))
@private_message
async def start(message: types.Message, state: FSMContext):
    await message.answer("Здесь <b>будет</b> список ваших групп.", parse_mode=ParseMode.HTML)