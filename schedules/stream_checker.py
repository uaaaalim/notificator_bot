import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from core.client import BotClient
from core.implementations.schedule import BaseSchedule
from services.http import request_json


class StreamPlatform(Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"


class Stream:
    platform: StreamPlatform = None
    title: str = None
    link: str = None
    started_at: datetime = None

    def __init__(self, platform: StreamPlatform, title: str, link: str, started_at: datetime):
        self.platform = platform
        self.title = title
        self.link = link
        self.started_at = started_at

    def __str__(self):
        return (f"Stream<platform={self.platform.name} link={self.link} started_at={self.started_at} "
                f"title={self.title}>")


class YoutubePlatform:
    def __init__(self, client: "BotClient"):
        self.client: "BotClient" = client

        self.youtube_api_key = self.client.config.youtube_api_key
        self.youtube_channel = self.client.config.youtube_channel

        self._upload_playlist_id: str | None = None
        self._live_video_id: str | None = None

    async def _ensure_upload_playlist_id(self) -> bool:
        if self._upload_playlist_id:
            return True

        url = "https://www.googleapis.com/youtube/v3/channels"

        params = {
            'part': 'snippet,contentDetails',
            'key': self.youtube_api_key
        }

        if self.youtube_channel.startswith("@"):
            params["forHandle"] = self.youtube_channel
        else:
            params["id"] = self.youtube_channel

        try:
            response = await request_json(
                self.client.http_session, 'GET', url,
                logger=self.client.logger,
                params=params,
            )

            items: list = response["items"]

            if len(items) == 0:
                self.client.logger.warning(
                    f"[youtube] YouTube channel {self.youtube_channel} was not found."
                )
                return False

            item = items[0]
            content = item["contentDetails"]
            playlists = content["relatedPlaylists"]
            self._upload_playlist_id = playlists["uploads"]

            snippet = item["snippet"]
            title = snippet["title"]

            self.client.logger.info(
                f"[youtube] Upload playlist (ID: {self._upload_playlist_id}) has been ensured for channel '{title}'"
            )

            return True
        except Exception as e:
            self.client.logger.error(
                f"[youtube] Failed to ensure upload playlist of channel '{self.youtube_channel}'", e
            )
            return False

    async def _get_live_video(self) -> Optional[list[str]]:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"

        try:
            response = await request_json(
                self.client.http_session, 'GET', url,
                params={
                    'playlistId': self._upload_playlist_id,
                    'part': 'snippet,contentDetails',
                    'maxResults': 3,
                    'key': self.youtube_api_key
                },
                logger=self.client.logger
            )

            items = response["items"]

            if not items:
                self.client.logger.warning(
                    f"[youtube] Videos from channel '{self.youtube_channel}' were not found'"
                )
                return None

            video_ids = []

            for item in items:
                snippet = item["snippet"]

                resource_id = snippet["resourceId"]
                video_ids.append(resource_id["videoId"])

            return video_ids
        except Exception as e:
            self.client.logger.error(
                f"[youtube] Failed to get videos from channel '{self.youtube_channel}'", e
            )
            return None

    async def get_stream(self) -> Optional[Stream]:
        ensured = await self._ensure_upload_playlist_id()

        if not ensured:
            self.client.logger.warning(
                f"[youtube] Couldn't get live from '{self.youtube_channel}': upload playlist is not available"
            )
            return None

        video_ids = await self._get_live_video()
        if not video_ids:
            return None

        url = "https://www.googleapis.com/youtube/v3/videos"

        try:
            response = await request_json(
                self.client.http_session, 'GET', url,
                params={
                    'id': ','.join(video_ids),
                    'part': 'snippet,liveStreamingDetails',
                    'key': self.youtube_api_key
                },
                logger=self.client.logger
            )

            items = response["items"]

            if not items:
                return None

            for item in items:
                snippet = item["snippet"]
                is_live = snippet["liveBroadcastContent"] == "live"

                if is_live:
                    title = snippet["title"]

                    streaming_details = item["liveStreamingDetails"]
                    started_at = datetime.fromisoformat(streaming_details["actualStartTime"].replace("Z", "+00:00"))

                    return Stream(
                        platform=StreamPlatform.YOUTUBE,
                        title=title,
                        link="https://www.youtube.com/watch?v=" + item["id"],
                        started_at=started_at
                    )

            return None
        except Exception as e:
            self.client.logger.error(
                f"[youtube] Failed to fetch video data from channel '{self.youtube_channel}'", e
            )
            return None


class TwitchPlatform:
    def __init__(self, client):
        self.client: "BotClient" = client

        self.twitch_client_id = self.client.config.twitch_client_id
        self.twitch_client_secret = self.client.config.twitch_client_secret
        self.twitch_channel_name = self.client.config.twitch_channel_name

        self._access_token: str | None = None
        self._token_expiry: datetime | None = None

    async def _ensure_twitch_token(self) -> bool:
        if self._access_token and self._token_expiry:
            if datetime.now(timezone.utc) < self._token_expiry:
                return True

        url = "https://id.twitch.tv/oauth2/token"

        try:
            response = await request_json(
                self.client.http_session, 'POST', url,
                params={
                    'client_id': self.twitch_client_id,
                    'client_secret': self.twitch_client_secret,
                    'grant_type': 'client_credentials'
                },
                logger=self.client.logger
            )

            access_token = response.get("access_token")
            expires_in = response.get("expires_in", 3600)

            if not access_token:
                self.client.logger.error(
                    "[twitch] Failed to get access token: No token presented"
                )
                return False

            self._access_token = access_token
            self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)

            self.client.logger.info("[twitch] Access token has been renewed")

            return True
        except Exception as e:
            self.client.logger.error(
                "[twitch] Failed to get access token", e
            )
            return False

    async def get_stream(self) -> Optional[Stream]:
        ensured = await self._ensure_twitch_token()

        if not ensured:
            self.client.logger.warning(
                f"[twitch] Couldn't get live from '{self.twitch_channel_name}': access token is not available"
            )
            return None

        url = "https://api.twitch.tv/helix/streams"

        try:
            response = await request_json(
                self.client.http_session, 'GET', url,
                params={
                    'user_login': self.twitch_channel_name
                },
                headers={
                    'Client-ID': self.twitch_client_id,
                    'Authorization': f"Bearer {self._access_token}"
                },
                logger=self.client.logger
            )

            streams = response.get("data", [])
            if not streams:
                return None

            stream = streams[0]

            title = stream["title"]
            started_at = datetime.fromisoformat(stream["started_at"].replace("Z", "+00:00"))

            return Stream(
                platform=StreamPlatform.TWITCH,
                title=title,
                link="https://www.twitch.tv/" + self.twitch_channel_name,
                started_at=started_at
            )
        except Exception as e:
            self.client.logger.error(
                f"[twitch] Failed to fetch video data from channel '{self.twitch_channel_name}'", e
            )
            return None


class StreamCheckerSchedule(BaseSchedule):
    delay_seconds = 10

    NORMAL_DELAY_NIGHT = 2 * 60
    NORMAL_DELAY_DAY = 15 * 60
    LIVE_DELAY = 10 * 60
    WAIT_SECOND_PLATFORM_DELAY = 30
    WAIT_SECOND_PLATFORM_ATTEMPTS = 5

    def __init__(self, client: "BotClient"):
        super().__init__(client)

        self.youtube = YoutubePlatform(client)
        self.twitch = TwitchPlatform(client)

        self._cached_live: list[Stream] = []

        self._waiting_attempt: int = 0

    def refresh_delay(self):
        now = datetime.now(timezone(timedelta(hours=3)))
        _delay = self.delay_seconds

        if self._cached_live:
            self.delay_seconds = self.LIVE_DELAY
        elif 3 <= now.hour < 15:
            self.delay_seconds = self.NORMAL_DELAY_DAY
        else:
            self.delay_seconds = self.NORMAL_DELAY_NIGHT

        if self.delay_seconds != _delay:
            self.client.logger.info(
                f"[stream_checker] The schedule cooldown has been set to {self.delay_seconds} seconds"
            )

    async def get_streams(self) -> list[Stream]:
        youtube_stream, twitch_stream = await asyncio.gather(
            self.youtube.get_stream(),
            self.twitch.get_stream(),
        )
        return [stream for stream in (youtube_stream, twitch_stream) if stream is not None]

    async def notify_content_author(self):
        self.client.logger.info("[stream_checker] Streams on following platforms were detected:")

        for stream in self._cached_live:
            self.client.logger.info(str(stream))

        self._waiting_attempt = 0
        self.refresh_delay()



    async def execute(self) -> None:
        streams = await self.get_streams()

        if not streams:
            if self._cached_live:
                self.client.logger.info("[stream_checker] Streams have been stopped (or broke)")

            self._cached_live = []
            self._waiting_attempt = 0
            self.refresh_delay()

            return

        if self._cached_live:
            return

        if len(streams) == 2:
            self._cached_live = streams
            await self.notify_content_author()

            return
        elif len(streams) == 1:
            if self._waiting_attempt >= self.WAIT_SECOND_PLATFORM_ATTEMPTS:
                self._cached_live = streams

                await self.notify_content_author()
                return

            self._waiting_attempt += 1
            self.delay_seconds = self.WAIT_SECOND_PLATFORM_DELAY

            self.client.logger.info(
                f"[stream_checker] Found stream on {streams[0].platform.name}, waiting for second one... "
                f"Attempt {self._waiting_attempt}/{self.WAIT_SECOND_PLATFORM_ATTEMPTS}"
            )
