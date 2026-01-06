from aiogram.fsm.state import StatesGroup, State


class AddBanWords(StatesGroup):
    waiting_for_words = State()
