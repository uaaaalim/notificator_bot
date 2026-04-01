import os

from dotenv import load_dotenv


class Config:
    def __init__(
            self, bot_token: str, database_url: str, log_level: str = "INFO", owner_ids: list[str] = None,
            db_pool_size: int = 20, db_max_overflow: int = 40, db_pool_recycle: int = 1800
    ) -> None:
        self.bot_token = bot_token
        self.database_url = database_url
        self.log_level = log_level
        self.owner_ids = [int(owner_id) for owner_id in (owner_ids or []) if str(owner_id).strip()]
        self.db_pool_size = db_pool_size
        self.db_max_overflow = db_max_overflow
        self.db_pool_recycle = db_pool_recycle


def _parse_owner_ids(raw_owner_ids: str | None) -> list[str]:
    if not raw_owner_ids:
        return []
    return [item.strip() for item in raw_owner_ids.split(",") if item.strip()]


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "") # telegram bot token
    database_url = os.getenv("DATABASE_URL", "") # strictly asynchronous postgresql connection, PostgreSQL 18 stable

    missing = [
        name for name, value in {
            "BOT_TOKEN": bot_token,
            "DATABASE_URL": database_url
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing env variables: {', '.join(missing)}")
    owner_ids = _parse_owner_ids(os.getenv("OWNER_IDS")) # telegram ids with owner-level access (e.g. /admin)

    log_level = os.getenv("LOG_LEVEL", "INFO")
    db_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))


    return Config(
        bot_token=bot_token, database_url=database_url, log_level=log_level, owner_ids=owner_ids,
        db_pool_size=db_pool_size, db_max_overflow=db_max_overflow, db_pool_recycle=db_pool_recycle
    )
