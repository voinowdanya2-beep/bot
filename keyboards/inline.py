from datetime import date, timedelta, datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import config


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Моя запись", callback_data="my_booking")],
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_booking")],
        [InlineKeyboardButton(text="💰 Прайсы", callback_data="prices")],
        [InlineKeyboardButton(text="📸 Портфолио", callback_data="portfolio")]
    ])


def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить рабочий день", callback_data="admin_add_day")],
        [InlineKeyboardButton(text="➕ Добавить слот", callback_data="admin_add_slot")],
        [InlineKeyboardButton(text="➖ Удалить слот", callback_data="admin_delete_slot")],
        [InlineKeyboardButton(text="🚫 Закрыть день", callback_data="admin_close_day")],
        [InlineKeyboardButton(text="✅ Открыть день", callback_data="admin_open_day")],
        [InlineKeyboardButton(text="📅 Расписание на дату", callback_data="admin_view_date")],
        [InlineKeyboardButton(text="❌ Отменить запись клиента", callback_data="admin_cancel_booking")]
    ])


def subscription_keyboard(channel_link: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url=channel_link)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])


def portfolio_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Смотреть портфолио", url=config.PORTFOLIO_LINK)]
    ])


def dates_keyboard(dates: list):
    buttons = []

    for item in dates:
        day = item[0]
        pretty = datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m.%Y")
        buttons.append([
            InlineKeyboardButton(text=pretty, callback_data=f"date:{day}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def month_calendar_keyboard(prefix: str):
    today = date.today()
    buttons = []

    row = []
    for i in range(31):
        current = today + timedelta(days=i)
        text = current.strftime("%d.%m")
        callback = f"{prefix}:{current.isoformat()}"
        row.append(InlineKeyboardButton(text=text, callback_data=callback))

        if len(row) == 4:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slots_keyboard(slots: list):
    buttons = []

    for slot_id, time in slots:
        buttons.append([
            InlineKeyboardButton(text=f"🕒 {time}", callback_data=f"slot:{slot_id}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="book")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])


def admin_slots_delete_keyboard(slots: list):
    buttons = []

    for slot in slots:
        slot_id, time, booking_id, user_id, name, phone, reminder_job_id = slot
        status = "занят" if booking_id else "свободен"
        buttons.append([
            InlineKeyboardButton(
                text=f"{time} — {status}",
                callback_data=f"admin_delete_slot_id:{slot_id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_bookings_keyboard(slots: list):
    buttons = []

    for slot in slots:
        slot_id, time, booking_id, user_id, name, phone, reminder_job_id = slot

        if booking_id:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{time} — {name}",
                    callback_data=f"admin_cancel_booking_id:{booking_id}"
                )
            ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
