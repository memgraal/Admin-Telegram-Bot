import asyncio

import aiogram
import dotenv


dotenv.load_dotenv()


async def main() -> None:
    bot = aiogram.Bot(token=dotenv.get_key("BOT_TOKEN"))
    dp = aiogram.Dispatcher(bot)

    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
