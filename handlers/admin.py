from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import config
from keyboards.inline import (
    admin_menu,
    month_calendar_keyboard,
    admin_slots_delete_keyboard,
    admin_bookings_keyboard
)
from states.booking import AdminFSM
from services.reminders import remove_reminder

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "<b>Админ-панель</b>",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    await callback.message.edit_text(
        "<b>Админ-панель</b>",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_add_day")
async def add_day(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.add_day_date)
    await callback.message.edit_text(
        "<b>Выберите рабочий день:</b>",
        reply_markup=month_calendar_keyboard("admin_day")
    )


@router.callback_query(AdminFSM.add_day_date, F.data.startswith("admin_day:"))
async def add_day_selected(callback: CallbackQuery, state: FSMContext, db):
    selected_date = callback.data.split(":")[1]

    default_times = ["10:00", "12:00", "14:00", "16:00", "18:00"]

    for time in default_times:
        await db.add_slot(selected_date, time)

    await state.clear()

    await callback.message.edit_text(
        f"<b>Рабочий день добавлен:</b> {selected_date}\n\n"
        "Созданы слоты: 10:00, 12:00, 14:00, 16:00, 18:00",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_add_slot")
async def add_slot_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.add_slot_date)
    await callback.message.edit_text(
        "<b>Выберите дату для добавления слота:</b>",
        reply_markup=month_calendar_keyboard("admin_add_slot_date")
    )


@router.callback_query(AdminFSM.add_slot_date, F.data.startswith("admin_add_slot_date:"))
async def add_slot_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split(":")[1]
    await state.update_data(date=selected_date)
    await state.set_state(AdminFSM.add_slot_time)

    await callback.message.edit_text(
        "<b>Введите время слота в формате HH:MM</b>\n\n"
        "Например: <code>13:30</code>"
    )


@router.message(AdminFSM.add_slot_time)
async def add_slot_time(message: Message, state: FSMContext, db):
    time = message.text.strip()

    if len(time) != 5 or ":" not in time:
        await message.answer("Введите время в формате HH:MM.")
        return

    data = await state.get_data()
    await db.add_slot(data["date"], time)
    await state.clear()

    await message.answer(
        f"<b>Слот добавлен:</b>\n{data['date']} — {time}",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_delete_slot")
async def delete_slot_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.delete_slot_date)
    await callback.message.edit_text(
        "<b>Выберите дату:</b>",
        reply_markup=month_calendar_keyboard("admin_delete_slot_date")
    )


@router.callback_query(AdminFSM.delete_slot_date, F.data.startswith("admin_delete_slot_date:"))
async def delete_slot_date(callback: CallbackQuery, db):
    selected_date = callback.data.split(":")[1]
    slots = await db.get_slots_by_date_admin(selected_date)

    if not slots:
        await callback.message.edit_text(
            "На эту дату слотов нет.",
            reply_markup=admin_menu()
        )
        return

    await callback.message.edit_text(
        f"<b>Выберите слот для удаления:</b>\n{selected_date}",
        reply_markup=admin_slots_delete_keyboard(slots)
    )


@router.callback_query(F.data.startswith("admin_delete_slot_id:"))
async def delete_slot_id(callback: CallbackQuery, db):
    if not is_admin(callback.from_user.id):
        return

    slot_id = int(callback.data.split(":")[1])
    await db.delete_slot(slot_id)

    await callback.message.edit_text(
        "<b>Слот удалён.</b>",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_close_day")
async def close_day_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.close_day_date)
    await callback.message.edit_text(
        "<b>Выберите день, который нужно закрыть:</b>",
        reply_markup=month_calendar_keyboard("admin_close_day_date")
    )


@router.callback_query(AdminFSM.close_day_date, F.data.startswith("admin_close_day_date:"))
async def close_day_date(callback: CallbackQuery, state: FSMContext, db):
    selected_date = callback.data.split(":")[1]
    await db.close_day(selected_date)
    await state.clear()

    await callback.message.edit_text(
        f"<b>День закрыт:</b> {selected_date}",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_open_day")
async def open_day_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.open_day_date)
    await callback.message.edit_text(
        "<b>Выберите день, который нужно открыть:</b>",
        reply_markup=month_calendar_keyboard("admin_open_day_date")
    )


@router.callback_query(AdminFSM.open_day_date, F.data.startswith("admin_open_day_date:"))
async def open_day_date(callback: CallbackQuery, state: FSMContext, db):
    selected_date = callback.data.split(":")[1]
    await db.open_day(selected_date)
    await state.clear()

    await callback.message.edit_text(
        f"<b>День открыт:</b> {selected_date}",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_view_date")
async def view_date_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.view_date)
    await callback.message.edit_text(
        "<b>Выберите дату для просмотра расписания:</b>",
        reply_markup=month_calendar_keyboard("admin_view_date_selected")
    )


@router.callback_query(AdminFSM.view_date, F.data.startswith("admin_view_date_selected:"))
async def view_date(callback: CallbackQuery, state: FSMContext, db):
    selected_date = callback.data.split(":")[1]
    slots = await db.get_slots_by_date_admin(selected_date)

    if not slots:
        text = f"<b>Расписание на {selected_date}</b>\n\nСлотов нет."
    else:
        lines = [f"<b>Расписание на {selected_date}</b>\n"]
        for slot_id, time, booking_id, user_id, name, phone, reminder_job_id in slots:
            if booking_id:
                lines.append(f"🔴 <b>{time}</b> — {name}, {phone}")
            else:
                lines.append(f"🟢 <b>{time}</b> — свободно")
        text = "\n".join(lines)

    await state.clear()

    await callback.message.edit_text(
        text,
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_cancel_booking")
async def cancel_booking_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminFSM.cancel_booking_date)
    await callback.message.edit_text(
        "<b>Выберите дату:</b>",
        reply_markup=month_calendar_keyboard("admin_cancel_booking_date")
    )


@router.callback_query(AdminFSM.cancel_booking_date, F.data.startswith("admin_cancel_booking_date:"))
async def cancel_booking_date(callback: CallbackQuery, db):
    selected_date = callback.data.split(":")[1]
    slots = await db.get_slots_by_date_admin(selected_date)

    has_bookings = any(slot[2] for slot in slots)

    if not has_bookings:
        await callback.message.edit_text(
            "На эту дату записей нет.",
            reply_markup=admin_menu()
        )
        return

    await callback.message.edit_text(
        f"<b>Выберите запись для отмены:</b>\n{selected_date}",
        reply_markup=admin_bookings_keyboard(slots)
    )


@router.callback_query(F.data.startswith("admin_cancel_booking_id:"))
async def admin_cancel_booking_id(callback: CallbackQuery, db, scheduler, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    booking_id = int(callback.data.split(":")[1])
    booking = await db.cancel_booking_by_id(booking_id)

    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    _, user_id, reminder_job_id = booking
    remove_reminder(scheduler, reminder_job_id)

    try:
        await bot.send_message(
            user_id,
            "<b>Ваша запись была отменена администратором.</b>"
        )
    except Exception:
        pass

    await callback.message.edit_text(
        "<b>Запись клиента отменена.</b>\nСлот снова доступен.",
        reply_markup=admin_menu()
    )
