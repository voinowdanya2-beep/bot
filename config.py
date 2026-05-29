import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))
    CHANNEL_LINK: str = os.getenv("CHANNEL_LINK", "")

    SCHEDULE_CHANNEL_ID: int = int(os.getenv("SCHEDULE_CHANNEL_ID", "0"))
    PORTFOLIO_LINK: str = os.getenv("PORTFOLIO_LINK", "https://t.me/your_portfolio_channel")

    DB_PATH: str = "manicure.db"


config = Config()
