import logging
import asyncio
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


async def main():
    # минимальный вывод
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.WARNING,
        filename="bot.log",
        filemode="a",
    )

    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.ERROR)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    engine = create_async_engine(
        os.getenv("DB_URL"),
        echo=False
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
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
