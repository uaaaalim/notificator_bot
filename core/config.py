import os

from dotenv import load_dotenv


class Config:
    def __init__(
            self, bot_token: str, database_url: str, log_level: str = "INFO",
            author_id: str | int = None, owner_ids: list[str | int] = None,
    ) -> None:
        self.bot_token = bot_token
        self.database_url = database_url
        self.log_level = log_level
        self.author_id = author_id
        self.owner_ids = owner_ids or []


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "")
    database_url = os.getenv("DATABASE_URL", "")
    if not bot_token or not database_url:
        raise ValueError("BOT_TOKEN is required in .env")

    author_id = os.getenv("AUTHOR_ID")
    owner_ids = os.getenv("OWNER_IDS").split(",")

    log_level = os.getenv("LOG_LEVEL", "INFO")


    return Config(
        bot_token=bot_token, database_url=database_url, log_level=log_level,
        author_id=author_id, owner_ids=owner_ids
    )
