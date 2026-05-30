import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = field(
    default_factory=lambda: [
        int(admin_id)
        for admin_id in os.getenv("ADMIN_IDS", "").split(",")
        if admin_id.strip()
    ]
)

    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))
    CHANNEL_LINK: str = os.getenv("CHANNEL_LINK", "")

    SCHEDULE_CHANNEL_ID: int = int(os.getenv("SCHEDULE_CHANNEL_ID", "0"))
    PORTFOLIO_LINK: str = os.getenv("PORTFOLIO_LINK", "https://t.me/your_portfolio_channel")

    DB_PATH: str = "manicure.db"


config = Config()
