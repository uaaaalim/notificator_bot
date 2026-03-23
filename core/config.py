import os

from dotenv import load_dotenv


class Config:
    def __init__(
            self, bot_token: str, database_url: str,
            youtube_api_key: str, youtube_channel_id: str,
            twitch_client_id: str, twitch_client_secret: str, twitch_channel_name: str,
            log_level: str = "INFO",
            author_id: str | int = None, owner_ids: list[str] = None,
            db_pool_size: int = 20, db_max_overflow: int = 40, db_pool_recycle: int = 1800
    ) -> None:
        self.bot_token = bot_token
        self.database_url = database_url
        self.log_level = log_level
        self.author_id = author_id
        self.owner_ids = map(int, owner_ids) or []
        self.db_pool_size = db_pool_size
        self.db_max_overflow = db_max_overflow
        self.db_pool_recycle = db_pool_recycle
        self.youtube_api_key = youtube_api_key
        self.youtube_channel_id = youtube_channel_id
        self.twitch_client_id = twitch_client_id
        self.twitch_client_secret = twitch_client_secret
        self.twitch_channel_name = twitch_channel_name


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "")
    database_url = os.getenv("DATABASE_URL", "")

    youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
    youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "")

    twitch_client_id = os.getenv("TWITCH_CLIENT_ID", "")
    twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET", "")
    twitch_channel_name = os.getenv("TWITCH_CHANNEL_NAME", "")

    missing = [
        name for name, value in {
            "BOT_TOKEN": bot_token,
            "DATABASE_URL": database_url,
            "YOUTUBE_API_KEY": youtube_api_key,
            "YOUTUBE_CHANNEL_ID": youtube_channel_id,
            "TWITCH_CLIENT_ID": twitch_client_id,
            "TWITCH_CLIENT_SECRET": twitch_client_secret,
            "TWITCH_CHANNEL_NAME": twitch_channel_name,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing env variables: {', '.join(missing)}")

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
        youtube_api_key=youtube_api_key, youtube_channel_id=youtube_channel_id,
        twitch_client_id=twitch_client_id,
        twitch_client_secret=twitch_client_secret,
        twitch_channel_name=twitch_channel_name,
    )
