import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import config
from database.db import Database
from handlers import user, admin
from services.reminders import restore_reminders




async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не указан в .env")


    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    db = Database(config.DB_PATH)
    await db.init()

    scheduler = AsyncIOScheduler()
    scheduler.start()

    await restore_reminders(db, scheduler, bot)

    # Эти объекты будут доступны в handlers через dependency injection aiogram
    dp["db"] = db
    dp["scheduler"] = scheduler

    dp.include_router(user.router)
    dp.include_router(admin.router)

    print("Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
