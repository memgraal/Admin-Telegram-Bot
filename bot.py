import os
import aiogram
import aiogram_fsm_sqlitestorage
from dotenv import load_dotenv

load_dotenv()

storage = aiogram_fsm_sqlitestorage.SQLiteStorage("states.db")

bot = aiogram.Bot(token=os.getenv("BOT_TOKEN"))
dp = aiogram.Dispatcher(storage=storage)
