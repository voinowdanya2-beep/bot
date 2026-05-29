from aiogram.fsm.state import StatesGroup, State


class BookingFSM(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()


class AdminFSM(StatesGroup):
    add_day_date = State()
    add_slot_date = State()
    add_slot_time = State()
    delete_slot_date = State()
    close_day_date = State()
    open_day_date = State()
    view_date = State()
    cancel_booking_date = State()
