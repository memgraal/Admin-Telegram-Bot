import asyncio
import os

import aiogram
from aiogram_fsm_sqlitestorage import SQLiteStorage
import dotenv
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import middlewares.db_middleware
import database

dotenv.load_dotenv()

storage = SQLiteStorage("states.db")

async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    engine = create_async_engine("sqlite+aiosqlite:///database.db", echo=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    bot = aiogram.Bot(token=os.getenv("BOT_TOKEN"))
    dp = aiogram.Dispatcher(storage=storage)

    dp.update.middleware(
        middlewares.db_middleware.DatabaseMiddleware(session_maker=session_maker),
    )
    
    import handlers.start
    dp.include_routers(handlers.start.router_start)

    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
