from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import config
from keyboards.inline import (
    main_menu,
    dates_keyboard,
    slots_keyboard,
    confirm_keyboard,
    subscription_keyboard,
    portfolio_keyboard
)
from states.booking import BookingFSM
from services.subscription import is_subscribed
from services.reminders import schedule_reminder, remove_reminder

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "<b>Добро пожаловать!</b>\n\n"
        "Здесь можно записаться на маникюр, посмотреть цены и портфолио.",
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "<b>Главное меню</b>",
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "prices")
async def prices(callback: CallbackQuery):
    await callback.message.answer(
        "<b>Прайсы</b>\n\n"
        "Френч — позже напишу ценник\n"
        "Квадрат — тоже позже"
    )
    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def portfolio(callback: CallbackQuery):
    await callback.message.answer(
        "<b>Портфолио</b>\n\n"
        "Нажмите кнопку ниже, чтобы посмотреть работы:",
        reply_markup=portfolio_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "book")
async def booking_start(callback: CallbackQuery, state: FSMContext, bot: Bot, db):
    subscribed = await is_subscribed(bot, callback.from_user.id)

    if not subscribed:
        await callback.message.edit_text(
            "Для записи необходимо подписаться на канал",
            reply_markup=subscription_keyboard(config.CHANNEL_LINK)
        )
        return

    existing = await db.user_has_booking(callback.from_user.id)

    if existing:
        _, visit_date, visit_time, name, phone, reminder_job_id = existing
        await callback.message.edit_text(
            "<b>У вас уже есть активная запись.</b>\n\n"
            f"Дата: <b>{visit_date}</b>\n"
            f"Время: <b>{visit_time}</b>\n"
            f"Имя: <b>{name}</b>\n"
            f"Телефон: <b>{phone}</b>",
            reply_markup=main_menu()
        )
        return

    dates = await db.get_available_dates()

    if not dates:
        await callback.message.edit_text(
            "<b>Свободных дат пока нет.</b>",
            reply_markup=main_menu()
        )
        return

    await state.set_state(BookingFSM.choosing_date)
    await callback.message.edit_text(
        "<b>Выберите дату:</b>",
        reply_markup=dates_keyboard(dates)
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot, db, state: FSMContext):
    subscribed = await is_subscribed(bot, callback.from_user.id)

    if not subscribed:
        await callback.answer("Вы ещё не подписались", show_alert=True)
        return

    dates = await db.get_available_dates()

    if not dates:
        await callback.message.edit_text(
            "<b>Подписка подтверждена.</b>\n\nСвободных дат пока нет.",
            reply_markup=main_menu()
        )
        return

    await state.set_state(BookingFSM.choosing_date)
    await callback.message.edit_text(
        "<b>Подписка подтверждена ✅</b>\n\nВыберите дату:",
        reply_markup=dates_keyboard(dates)
    )


@router.callback_query(BookingFSM.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, db):
    selected_date = callback.data.split(":")[1]
    slots = await db.get_available_slots_by_date(selected_date)

    if not slots:
        await callback.answer("На эту дату нет свободного времени", show_alert=True)
        return

    await state.update_data(date=selected_date)
    await state.set_state(BookingFSM.choosing_time)

    await callback.message.edit_text(
        f"<b>Дата:</b> {selected_date}\n\nВыберите свободное время:",
        reply_markup=slots_keyboard(slots)
    )


@router.callback_query(BookingFSM.choosing_time, F.data.startswith("slot:"))
async def choose_slot(callback: CallbackQuery, state: FSMContext, db):
    slot_id = int(callback.data.split(":")[1])
    slot = await db.get_slot(slot_id)

    if not slot:
        await callback.answer("Слот не найден", show_alert=True)
        return

    await state.update_data(slot_id=slot_id, date=slot[1], time=slot[2])
    await state.set_state(BookingFSM.entering_name)

    await callback.message.edit_text("<b>Введите ваше имя:</b>")


@router.message(BookingFSM.entering_name)
async def enter_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Введите нормальное имя.")
        return

    await state.update_data(name=name)
    await state.set_state(BookingFSM.entering_phone)

    await message.answer("<b>Введите номер телефона:</b>")


@router.message(BookingFSM.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    phone = message.text.strip()

    if len(phone) < 6:
        await message.answer("Введите корректный номер телефона.")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()

    await state.set_state(BookingFSM.confirming)

    await message.answer(
        "<b>Проверьте запись:</b>\n\n"
        f"Дата: <b>{data['date']}</b>\n"
        f"Время: <b>{data['time']}</b>\n"
        f"Имя: <b>{data['name']}</b>\n"
        f"Телефон: <b>{data['phone']}</b>",
        reply_markup=confirm_keyboard()
    )


@router.callback_query(BookingFSM.confirming, F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db, bot: Bot, scheduler):
    user_id = callback.from_user.id

    existing = await db.user_has_booking(user_id)
    if existing:
        await state.clear()
        await callback.message.edit_text(
            "У вас уже есть активная запись.",
            reply_markup=main_menu()
        )
        return

    data = await state.get_data()

    booking_id = await db.create_booking(
        user_id=user_id,
        username=callback.from_user.username,
        name=data["name"],
        phone=data["phone"],
        slot_id=data["slot_id"],
        reminder_job_id=None
    )

    job_id = schedule_reminder(
        scheduler=scheduler,
        bot=bot,
        booking_id=booking_id,
        user_id=user_id,
        visit_date=data["date"],
        visit_time=data["time"]
    )

    await db.update_booking_reminder(booking_id, job_id)

    admin_text = (
        "<b>Новая запись 💅</b>\n\n"
        f"Дата: <b>{data['date']}</b>\n"
        f"Время: <b>{data['time']}</b>\n"
        f"Имя: <b>{data['name']}</b>\n"
        f"Телефон: <b>{data['phone']}</b>\n"
        f"Telegram: @{callback.from_user.username or 'без username'}\n"
        f"ID: <code>{user_id}</code>"
    )

    await bot.send_message(config.ADMIN_ID, admin_text)

    if config.SCHEDULE_CHANNEL_ID:
        await bot.send_message(
            config.SCHEDULE_CHANNEL_ID,
            "<b>Запись в расписании</b>\n\n"
            f"Дата: <b>{data['date']}</b>\n"
            f"Время: <b>{data['time']}</b>\n"
            f"Клиент: <b>{data['name']}</b>"
        )

    await state.clear()

    await callback.message.edit_text(
        "<b>Запись подтверждена ✅</b>\n\n"
        f"Дата: <b>{data['date']}</b>\n"
        f"Время: <b>{data['time']}</b>",
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "my_booking")
async def my_booking(callback: CallbackQuery, db):
    booking = await db.user_has_booking(callback.from_user.id)

    if not booking:
        await callback.message.edit_text(
            "У вас нет активной записи.",
            reply_markup=main_menu()
        )
        return

    _, visit_date, visit_time, name, phone, reminder_job_id = booking

    await callback.message.edit_text(
        "<b>Ваша запись:</b>\n\n"
        f"Дата: <b>{visit_date}</b>\n"
        f"Время: <b>{visit_time}</b>\n"
        f"Имя: <b>{name}</b>\n"
        f"Телефон: <b>{phone}</b>",
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "cancel_my_booking")
async def cancel_my_booking(callback: CallbackQuery, db, scheduler):
    booking = await db.cancel_booking_by_user(callback.from_user.id)

    if not booking:
        await callback.message.edit_text(
            "У вас нет активной записи.",
            reply_markup=main_menu()
        )
        return

    _, reminder_job_id = booking
    remove_reminder(scheduler, reminder_job_id)

    await callback.message.edit_text(
        "<b>Запись отменена.</b>\n\nСлот снова стал доступен.",
        reply_markup=main_menu()
    )
