import os

from dotenv import load_dotenv


class Config:
    def __init__(
            self, bot_token: str, database_url: str, log_level: str = "INFO",
            author_id: str | int = None, owner_ids: list[str | int] = None,
            db_pool_size: int = 20, db_max_overflow: int = 40, db_pool_recycle: int = 1800,
    ) -> None:
        self.bot_token = bot_token
        self.database_url = database_url
        self.log_level = log_level
        self.author_id = author_id
        self.owner_ids = owner_ids or []
        self.db_pool_size = db_pool_size
        self.db_max_overflow = db_max_overflow
        self.db_pool_recycle = db_pool_recycle


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "")
    database_url = os.getenv("DATABASE_URL", "")
    if not bot_token or not database_url:
        raise ValueError("BOT_TOKEN is required in .env")

    author_id = os.getenv("AUTHOR_ID")
    owner_ids = os.getenv("OWNER_IDS").split(",")

    log_level = os.getenv("LOG_LEVEL", "INFO")
    db_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))


    return Config(
        bot_token=bot_token, database_url=database_url, log_level=log_level,
        author_id=author_id, owner_ids=owner_ids,
        db_pool_size=db_pool_size, db_max_overflow=db_max_overflow, db_pool_recycle=db_pool_recycle,
    )
