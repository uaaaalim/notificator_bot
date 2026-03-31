import os

from dotenv import load_dotenv


class Config:
    def __init__(
            self, bot_token: str, database_url: str,
            youtube_api_key: str, youtube_channel: str,
            twitch_client_id: str, twitch_client_secret: str, twitch_channel_name: str,
            log_level: str = "INFO",
            author_id: str | int = None, author_channel_id: str | int = None, owner_ids: list[str] = None,
            db_pool_size: int = 20, db_max_overflow: int = 40, db_pool_recycle: int = 1800
    ) -> None:
        self.bot_token = bot_token
        self.database_url = database_url
        self.log_level = log_level
        self.author_id = author_id
        self.author_channel_id = author_channel_id
        self.owner_ids = [int(owner_id) for owner_id in (owner_ids or []) if str(owner_id).strip()]
        self.db_pool_size = db_pool_size
        self.db_max_overflow = db_max_overflow
        self.db_pool_recycle = db_pool_recycle
        self.youtube_api_key = youtube_api_key
        self.youtube_channel = youtube_channel
        self.twitch_client_id = twitch_client_id
        self.twitch_client_secret = twitch_client_secret
        self.twitch_channel_name = twitch_channel_name


def _parse_owner_ids(raw_owner_ids: str | None) -> list[str]:
    if not raw_owner_ids:
        return []
    return [item.strip() for item in raw_owner_ids.split(",") if item.strip()]


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "") # telegram bot token
    database_url = os.getenv("DATABASE_URL", "") # strictly asynchronous postgresql connection, PostgreSQL 18 stable

    youtube_api_key = os.getenv("YOUTUBE_API_KEY", "") # api key for youtube from googleapis
    youtube_channel = os.getenv("YOUTUBE_CHANNEL", "") # @somechannel or UC_CHANNEL_ID

    twitch_client_id = os.getenv("TWITCH_CLIENT_ID", "") # client id from twitch dev portal
    twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET", "") # client secret
    twitch_channel_name = os.getenv("TWITCH_CHANNEL_NAME", "") # channel name (username without @ in the beginning)

    author_id = os.getenv("AUTHOR_ID") # content author's telegram id (who confirms stream topics before notifications)

    missing = [
        name for name, value in {
            "BOT_TOKEN": bot_token,
            "DATABASE_URL": database_url,
            "YOUTUBE_API_KEY": youtube_api_key,
            "YOUTUBE_CHANNEL": youtube_channel,
            "TWITCH_CLIENT_ID": twitch_client_id,
            "TWITCH_CLIENT_SECRET": twitch_client_secret,
            "TWITCH_CHANNEL_NAME": twitch_channel_name,
            "AUTHOR_ID": author_id
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing env variables: {', '.join(missing)}")
    owner_ids = _parse_owner_ids(os.getenv("OWNER_IDS")) # telegram ids with owner-level access (e.g. /admin)

    author_channel_id = os.getenv("AUTHOR_CHANNEL_ID") # optional telegram channel id for public announcements

    log_level = os.getenv("LOG_LEVEL", "INFO")
    db_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))


    return Config(
        bot_token=bot_token, database_url=database_url, log_level=log_level,
        author_id=author_id, author_channel_id=author_channel_id, owner_ids=owner_ids,
        db_pool_size=db_pool_size, db_max_overflow=db_max_overflow, db_pool_recycle=db_pool_recycle,
        youtube_api_key=youtube_api_key, youtube_channel=youtube_channel,
        twitch_client_id=twitch_client_id,
        twitch_client_secret=twitch_client_secret,
        twitch_channel_name=twitch_channel_name,
    )
