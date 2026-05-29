import aiosqlite
from datetime import datetime


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    UNIQUE(date, time)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    slot_id INTEGER NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    reminder_job_id TEXT,
                    FOREIGN KEY(slot_id) REFERENCES slots(id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS closed_days (
                    date TEXT PRIMARY KEY
                )
            """)

            await db.commit()

    async def add_slot(self, date: str, time: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO slots(date, time) VALUES(?, ?)",
                (date, time)
            )
            await db.commit()

    async def delete_slot(self, slot_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM bookings WHERE slot_id = ?", (slot_id,))
            await db.execute("DELETE FROM slots WHERE id = ?", (slot_id,))
            await db.commit()

    async def get_available_dates(self):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT s.date
                FROM slots s
                LEFT JOIN bookings b ON b.slot_id = s.id
                LEFT JOIN closed_days c ON c.date = s.date
                WHERE b.id IS NULL
                  AND c.date IS NULL
                  AND date(s.date) >= date('now')
                  AND date(s.date) <= date('now', '+1 month')
                ORDER BY s.date
            """)
            return await cursor.fetchall()

    async def get_available_slots_by_date(self, date: str):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT s.id, s.time
                FROM slots s
                LEFT JOIN bookings b ON b.slot_id = s.id
                LEFT JOIN closed_days c ON c.date = s.date
                WHERE s.date = ?
                  AND b.id IS NULL
                  AND c.date IS NULL
                ORDER BY s.time
            """, (date,))
            return await cursor.fetchall()

    async def get_slots_by_date_admin(self, date: str):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT
                    s.id, s.time,
                    b.id,
                    b.user_id,
                    b.name,
                    b.phone,
                    b.reminder_job_id
                FROM slots s
                LEFT JOIN bookings b ON b.slot_id = s.id
                WHERE s.date = ?
                ORDER BY s.time
            """, (date,))
            return await cursor.fetchall()

    async def user_has_booking(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT b.id, s.date, s.time, b.name, b.phone, b.reminder_job_id
                FROM bookings b
                JOIN slots s ON s.id = b.slot_id
                WHERE b.user_id = ?
            """, (user_id,))
            return await cursor.fetchone()

    async def create_booking(
        self,
        user_id: int,
        username: str | None,
        name: str,
        phone: str,
        slot_id: int,
        reminder_job_id: str | None = None
    ):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                INSERT INTO bookings(
                    user_id, username, name, phone, slot_id, created_at, reminder_job_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                username,
                name,
                phone,
                slot_id,
                datetime.now().isoformat(),
                reminder_job_id
            ))
            await db.commit()
            return cursor.lastrowid

    async def update_booking_reminder(self, booking_id: int, reminder_job_id: str | None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE bookings SET reminder_job_id = ? WHERE id = ?",
                (reminder_job_id, booking_id)
            )
            await db.commit()

    async def get_slot(self, slot_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, date, time FROM slots WHERE id = ?",
                (slot_id,)
            )
            return await cursor.fetchone()

    async def cancel_booking_by_user(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT id, reminder_job_id
                FROM bookings
                WHERE user_id = ?
            """, (user_id,))
            booking = await cursor.fetchone()

            if not booking:
                return None

            await db.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
            await db.commit()
            return booking

    async def cancel_booking_by_id(self, booking_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT id, user_id, reminder_job_id
                FROM bookings
                WHERE id = ?
            """, (booking_id,))
            booking = await cursor.fetchone()

            if not booking:
                return None

            await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            await db.commit()
            return booking

    async def close_day(self, date: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO closed_days(date) VALUES(?)", (date,))
            await db.commit()

    async def open_day(self, date: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM closed_days WHERE date = ?", (date,))
            await db.commit()

    async def get_active_bookings_for_reminders(self):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("""
                SELECT b.id, b.user_id, s.date, s.time
                FROM bookings b
                JOIN slots s ON s.id = b.slot_id
            """)
            return await cursor.fetchall()
