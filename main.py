import asyncio
import logging
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot import bot, dp
import database
import handlers.banwords
import handlers.captcha
import handlers.init_group
import handlers.start
import middlewares.db_middleware

load_dotenv()


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
