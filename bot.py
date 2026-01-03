import asyncio
import aiogram
from aiogram_fsm_sqlitestorage import SQLiteStorage
import dotenv
import logging


dotenv.load_dotenv()

storage = SQLiteStorage("states.db")

async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    bot = aiogram.Bot(token=dotenv.get_key("BOT_TOKEN"))
    dp = aiogram.Dispatcher(storage=storage)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
