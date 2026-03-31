import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import selectinload

from core.client import BotClient
from core.implementations.schedule import BaseSchedule
from database.entities.subscribers import SubscriberEntity
from database.entities.stream_topic import StreamTopicEntity
from database.services.configs import get_config
from database.services.stream_topics import get_stream_topics
from database.services.subscribers import get_subscribers
from services.emojis import live_emojis, LIGHTENING_EMOJI, YOUTUBE_EMOJI_ID, TWITCH_EMOJI_ID, YOUTUBE_EMOJI, \
    TWITCH_EMOJI, LIGHTENING_EMOJI_ID, render_emoji
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
                f"[youtube] Failed to ensure upload playlist of channel '{self.youtube_channel}': {e}"
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
                f"[youtube] Failed to get videos from channel '{self.youtube_channel}': {e}"
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
                f"[youtube] Failed to fetch video data from channel '{self.youtube_channel}': {e}"
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
                f"[twitch] Failed to get access token: {e}"
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
                f"[twitch] Failed to fetch video data from channel '{self.twitch_channel_name}': {e.args}"
            )
            return None


class StreamCheckerSchedule(BaseSchedule):
    delay_seconds = 10

    NORMAL_DELAY_NIGHT = 2 * 60
    NORMAL_DELAY_DAY = 15 * 60
    LIVE_DELAY = 10 * 60
    WAIT_SECOND_PLATFORM_DELAY = 30
    WAIT_SECOND_PLATFORM_ATTEMPTS = 5
    WAIT_TOPICS_FROM_AUTHOR_TIMEOUT = 3 * 60

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

    def _get_emoji(self, emoji: Optional[str], default_emoji: str = "📃") -> str:
        if emoji:
            if emoji.isdigit():
                return render_emoji(emoji, default_emoji)
            else:
                return emoji

        return default_emoji

    def _get_priority_stream(self) -> Optional[Stream]:
        youtube_streams = [stream for stream in self._cached_live if stream.platform == StreamPlatform.YOUTUBE]
        if youtube_streams:
            return youtube_streams[0]

        twitch_streams = [stream for stream in self._cached_live if stream.platform == StreamPlatform.TWITCH]
        if twitch_streams:
            return twitch_streams[0]

        return None

    async def get_streams(self) -> list[Stream]:
        youtube_stream, twitch_stream = await asyncio.gather(
            self.youtube.get_stream(),
            self.twitch.get_stream(),
        )
        return [stream for stream in (youtube_stream, twitch_stream) if stream is not None]

    async def _recognize_topics(self, topics: list[StreamTopicEntity]) -> list[StreamTopicEntity]:
        if not topics:
            self.client.logger.warning(
                "[stream_checker] Topics haven't been configured yet. Skipping recognition..."
            )
            return []
        elif not self._cached_live:
            self.client.logger.warning(
                "[stream_checker] Live streams are not cached now. Skipping recognition..."
            )
            return []

        recognized_topics: list[StreamTopicEntity] = []
        now_msk = datetime.now(timezone(timedelta(hours=3)))

        for topic in topics:
            matched = False

            if now_msk.hour >= 20 and topic.is_night:
                matched = True
            elif 12 <= now_msk.hour < 20 and topic.is_main:
                matched = True

            for stream in self._cached_live:
                if (
                        stream.platform == StreamPlatform.YOUTUBE and topic.is_youtube
                ) or (
                        stream.platform == StreamPlatform.TWITCH and topic.is_twitch
                ):
                    matched = True
                    break

            if matched and topic not in recognized_topics:
                recognized_topics.append(topic)

        priority_stream = self._get_priority_stream()
        if not priority_stream:
            self.client.logger.warning(
                "[stream_checker] Priority stream is not recognized yet. Mistery >:("
            )
            return recognized_topics

        stream_title = priority_stream.title.lower()
        for topic in topics:
            if not topic.triggers:
                continue

            for trigger in topic.triggers.split(", "):
                if trigger.lower() in stream_title and topic not in recognized_topics:
                    recognized_topics.append(topic)

        return recognized_topics

    def _get_notify_data(self) -> list[str]:
        priority_stream = self._get_priority_stream()

        notify_data = [
            f"{LIGHTENING_EMOJI} <b>{priority_stream.title}</b>\n",
        ]
        for stream in self._cached_live:
            if stream.platform == StreamPlatform.YOUTUBE:
                notify_data.append(f"{YOUTUBE_EMOJI} <b><a href=\"{stream.link}\">Смотри сейчас на YouTube!</a></b>")
            elif stream.platform == StreamPlatform.TWITCH:
                notify_data.append(f"{TWITCH_EMOJI} <b><a href=\"{stream.link}\">Смотри сейчас на Twitch!</a></b>")

        return notify_data

    def _build_author_notify_message(
            self,
            recognized_topics: list[StreamTopicEntity]
    ) -> str:
        recognized_text = ("\n".join(map(
            lambda t: "- " + self._get_emoji(t.emoji) + " " + t.name, recognized_topics))
            if recognized_topics else "❌ Теги стрима не определены автоматически :("
        )
        notify_lines = "\n".join(self._get_notify_data())

        return (f"{live_emojis()}\n\n"
                f"{notify_lines}\n\n"
                "Определенные мною теги стрима:\n"
                f"{recognized_text}\n\n"
                "⚠️ У вас есть <b>3 минуты</b>, чтобы изменить выбранные тематики")

    def _build_topic_selection_keyboard(
            self,
            selected_topics: list[StreamTopicEntity],
            topics: list[StreamTopicEntity]
    ):
        buttons = []

        for topic in topics:
            text = ""
            emoji = None

            if topic.emoji and topic.emoji.isdigit():
                emoji = topic.emoji
            else:
                text += (topic.emoji if topic.emoji else "📃") + " "

            text += topic.name

            if topic in selected_topics:
                text += " ✅ (Выбрано)"
            else:
                text += " ⬜"

            buttons.append([InlineKeyboardButton(text=text, callback_data="notify_tag:" + str(topic.id),
                                                 icon_custom_emoji_id=emoji)])

        buttons.append([InlineKeyboardButton(text="🔔 Сохранить", callback_data="notify_tag:save")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def _build_notify_keyboard(self) -> InlineKeyboardMarkup:
        notify_keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for stream in self._cached_live:
            if stream.platform == StreamPlatform.YOUTUBE:
                notify_keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="Смотри сейчас на YouTube!", url=stream.link,
                                         icon_custom_emoji_id=YOUTUBE_EMOJI_ID)
                ])
            elif stream.platform == StreamPlatform.TWITCH:
                notify_keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="Смотри сейчас на Twitch!", url=stream.link,
                                         icon_custom_emoji_id=TWITCH_EMOJI_ID)
                ])

        return notify_keyboard

    def _build_notify_message(self, selected_topics: list[StreamTopicEntity]) -> list[str]:
        notify_lines = "\n".join(self._get_notify_data())
        message = [
            f"{live_emojis()}\n",
            f"{notify_lines}\n"
        ]

        if selected_topics:
            topic_lines = "\n".join(map(
                lambda t: "- " + (self._get_emoji(t.emoji)) + " " + t.name,
                selected_topics,
            ))

            message.append(f"Теги стрима:\n{topic_lines}\n")

        return message

    async def notify_content_author(self) -> None:
        platforms = ""
        for stream in self._cached_live:
            platforms += f"[{stream.platform.name}: {stream.link}] "

        self.client.logger.info("[stream_checker] Detected streams: " + platforms)

        self._waiting_attempt = 0
        self.refresh_delay()

        async with self.client.db.session() as session:
            topics = list(await get_stream_topics(session))

            config = {
                'wait_for_tags': await get_config(session, 'streams_wait_for_tags', '1') == '1',
                'notify_channel': await get_config(session, 'streams_notify_channel', '1') == '1',
                'notify_subscribers': await get_config(session, 'streams_notify_subscribers', '1') == '1'
            }

            subscribers = await get_subscribers(
                session,
                options=[selectinload(SubscriberEntity.stream_topics)],
            )

        selected_topics: list[StreamTopicEntity] = await self._recognize_topics(topics)
        content_author_id: int | str = self.client.config.author_id

        prompt = await self.client.bot.send_message(
            content_author_id,
            text=self._build_author_notify_message(selected_topics),
            reply_markup=self._build_topic_selection_keyboard(selected_topics, topics),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        async def on_timeout():
            approved_topics_text = (
                "\n".join(map(
                    lambda t: "- " + self._get_emoji(t.emoji) + " " + t.name, selected_topics))
                    if selected_topics else "❌ Теги стрима не выбраны :("
            )
            status_text = (
                "Уведомление подписчикам уже летит!"
                if selected_topics
                else "Я не смогу уведомить подписчиков лично, поскольку теги стрима не выбраны"
            )
            notify_lines = "\n".join(self._get_notify_data())

            await prompt.edit_text(
                text=f"{live_emojis()}\n\n"
                     f"{notify_lines}\n\n"
                     "Утвержденные теги стрима:\n"
                     f"{approved_topics_text}\n\n"
                     f"⚠️ {status_text}",
                parse_mode="HTML",
                reply_markup=None,
                disable_web_page_preview=True
            )

        while True:
            if not config['wait_for_tags']:
                await on_timeout()
                break

            callback = await self.client.wait_for_button(
                chat_id=prompt.chat.id,
                user_id=int(content_author_id),
                timeout=self.WAIT_TOPICS_FROM_AUTHOR_TIMEOUT,
                message_id=prompt.message_id,
                on_timeout=on_timeout
            )

            if not callback or not callback.data.startswith("notify_tag:"):
                break

            data = callback.data.split(":")[1]

            if data == "save":
                await on_timeout()
                break

            for topic in topics:
                if str(topic.id) == data:
                    if topic in selected_topics:
                        selected_topics.remove(topic)
                    else:
                        selected_topics.append(topic)

                    await prompt.edit_text(
                        text=self._build_author_notify_message(selected_topics),
                        reply_markup=self._build_topic_selection_keyboard(selected_topics, topics),
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )

        if config['notify_channel']:
            channel_id = self.client.config.author_channel_id

            if not channel_id:
                self.client.logger.warning("[stream_checker] Content author channel id is not set, skipping...")
            else:
                notify_message = self._build_notify_message(selected_topics)
                notify_keyboard = self._build_notify_keyboard()

                me = await self.client.bot.get_me()

                notify_message.append(
                    f"{LIGHTENING_EMOJI} Вы можете получать уведомления <b>лично</b>! Жми кнопку ниже!"
                )
                notify_keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"{LIGHTENING_EMOJI} Получать уведомления лично!", url="https://t.me/" + me.username
                    )
                ])

                try:
                    await self.client.bot.send_message(
                        channel_id,
                        text='\n'.join(notify_message),
                        reply_markup=notify_keyboard,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    self.client.logger.info(
                        f"[stream_checker] The announcement has been sent to channel {channel_id}"
                    )
                except TelegramForbiddenError:
                    self.client.logger.warning(
                        f"[stream_checker] Couldn't send the announcement to channel {channel_id}: Not available."
                    )
                except TelegramBadRequest as e:
                    self.client.logger.error(
                        f"[stream_checker] Couldn't send the announcement to channel {channel_id}: {e}"
                    )
                except Exception as e:
                    self.client.logger.error(
                        f"[stream_checker] Couldn't send the announcement to channel {channel_id}: {e}"
                    )

        if config['notify_subscribers'] and selected_topics:
            notify_message = self._build_notify_message(selected_topics)
            notify_keyboard = self._build_notify_keyboard()
            selected_topic_ids = {topic.id for topic in selected_topics}

            notify_message.append("🔔 Вам пришло уведомление, потому что вы подписаны на тематики стримов!")
            notify_keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="Изменить тематики стримов", callback_data="choose_stream_topics",
                    icon_custom_emoji_id=LIGHTENING_EMOJI_ID
                )
            ])

            sent = 0
            errored = 0

            for subscriber in subscribers:
                subscriber_topic_ids = {topic.id for topic in subscriber.stream_topics}
                if not (selected_topic_ids & subscriber_topic_ids):
                    continue

                try:
                    await self.client.bot.send_message(
                        subscriber.tg_id,
                        text='\n'.join(notify_message),
                        reply_markup=notify_keyboard,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                    sent += 1

                    await asyncio.sleep(0.01)
                except TelegramForbiddenError:
                    errored += 1
                except TelegramBadRequest as e:
                    errored += 1
                    self.client.logger.error(
                        f"[stream_checker] Couldn't send the announcement to subscriber {subscriber.tg_id}: {e}"
                    )
                except Exception as e:
                    errored += 1
                    self.client.logger.error(
                        f"[stream_checker] Couldn't send the announcement to subscriber {subscriber.tg_id}: {e}"
                    )

            self.client.logger.info(
                f"[stream_checker] The announcement has been sent to {sent} users ({errored} fails)"
            )

    async def execute(self) -> None:
        streams = await self.get_streams()

        if not streams:
            if self._cached_live:
                self.client.logger.info("[stream_checker] Streams have been stopped (or broken)")

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
