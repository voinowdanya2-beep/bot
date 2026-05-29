from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot


def make_job_id(booking_id: int) -> str:
    return f"booking_reminder_{booking_id}"


async def send_reminder(bot: Bot, user_id: int, time: str):
    await bot.send_message(
        user_id,
        f"Напоминаем, что вы записаны на наращивание ресниц завтра в <b>{time}</b>.\nЖдём вас ❤️",
        parse_mode="HTML"
    )


def schedule_reminder(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    booking_id: int,
    user_id: int,
    visit_date: str,
    visit_time: str
) -> str | None:
    visit_dt = datetime.strptime(f"{visit_date} {visit_time}", "%Y-%m-%d %H:%M")
    reminder_dt = visit_dt - timedelta(hours=24)

    if reminder_dt <= datetime.now():
        return None

    job_id = make_job_id(booking_id)

    scheduler.add_job(
        send_reminder,
        trigger="date",
        run_date=reminder_dt,
        args=[bot, user_id, visit_time],
        id=job_id,
        replace_existing=True
    )

    return job_id


def remove_reminder(scheduler: AsyncIOScheduler, job_id: str | None):
    if not job_id:
        return

    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


async def restore_reminders(db, scheduler: AsyncIOScheduler, bot: Bot):
    bookings = await db.get_active_bookings_for_reminders()

    for booking_id, user_id, visit_date, visit_time in bookings:
        job_id = schedule_reminder(
            scheduler=scheduler,
            bot=bot,
            booking_id=booking_id,
            user_id=user_id,
            visit_date=visit_date,
            visit_time=visit_time
        )
        await db.update_booking_reminder(booking_id, job_id)
