import datetime
from enum import Enum

import aiohttp

from core.implementations.schedule import BaseSchedule


class StreamPlatform(Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"


class Stream:
    platform: StreamPlatform = None
    title: str = None
    link: str = None
    started_at: datetime.datetime = None

    def __init__(self, platform: StreamPlatform, title: str, link: str, started_at: datetime.datetime):
        self.platform = platform
        self.title = title
        self.link = link
        self.started_at = started_at


class StreamCheckerSchedule(BaseSchedule):
    delay_seconds = 120 # seconds

    def __init__(self, client):
        super().__init__(client)

        self._access_token: str | None = None
        self._token_expiry: datetime.datetime | None = None

    async def _ensure_twitch_token(self, session: aiohttp.ClientSession):
        if self._access_token and self._token_expiry:
            if datetime.datetime.now(datetime.UTC) < self._token_expiry:
                return  # token still valid

        oauth_url = (
            "https://id.twitch.tv/oauth2/token"
            f"?client_id={self.client.config.twitch_client_id}"
            f"&client_secret={self.client.config.twitch_client_secret}"
            "&grant_type=client_credentials"
        )

        async with session.post(oauth_url) as resp:
            token_data = await resp.json()

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token:
            raise RuntimeError("Twitch auth failed")

        self._access_token = access_token
        self._token_expiry = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=expires_in - 60)

        self.client.logger.info("[stream_checker] Twitch access token has been renewed")

    async def get_twitch_live(self):
        async with aiohttp.ClientSession() as session:
            await self._ensure_twitch_token(session)

            headers = {
                "Client-ID": self.client.config.twitch_client_id,
                "Authorization": f"Bearer {self._access_token}"
            }
            stream_url = (
                "https://api.twitch.tv/helix/streams"
                f"?user_login={self.client.config.twitch_channel_name}"
            )

            async with session.get(stream_url, headers=headers) as resp:
                data = await resp.json()

            streams = data.get("data", [])
            if not streams:
                return None

            s = streams[0]

            title = s.get("title")
            started_at = s.get("started_at")
            start_dt = datetime.datetime.fromisoformat(started_at.replace("Z", "+00:00"))

            return Stream(
                platform=StreamPlatform.TWITCH,
                title=title,
                link="https://twitch.tv/" + self.client.config.twitch_channel_name,
                started_at=start_dt
            )

    async def execute(self) -> None:
        print(1)