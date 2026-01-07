import asyncio
import os
import logging

import aiogram
from aiogram_fsm_sqlitestorage import SQLiteStorage
import dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import middlewares.db_middleware
import database


dotenv.load_dotenv()

storage = SQLiteStorage("states.db")

bot = aiogram.Bot(token=os.getenv("BOT_TOKEN"))
dp = aiogram.Dispatcher(storage=storage)


async def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    engine = create_async_engine(
        os.getenv("DB_URL"),
        echo=True
    )
    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    dp.update.middleware(
        middlewares.db_middleware.DatabaseMiddleware(session_maker)
    )

    import handlers.start
    import handlers.init_group
    import handlers.banwords
    import handlers.captcha

    dp.include_routers(
        handlers.start.router_start,
        handlers.init_group.router_init_group,
        handlers.captcha.router_captcha,
        handlers.banwords.router_banwords,
    )

    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
                "my_chat_member",
            ],
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
