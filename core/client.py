import asyncio
from datetime import datetime, UTC

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from core.config import load_config
from core.database.session import Database
from core.implementations.button import BaseButton
from core.implementations.command import BaseCommand
from core.implementations.message import BaseMessage
from core.implementations.schedule import BaseSchedule
from core.loader import load_instances_from_directory
from core.logger import setup_logger
from core.waiter import EventWaiter


class BotClient:
    def __init__(self) -> None:
        self.config = load_config()
        self.logger = setup_logger(self.config.log_level)
        self.uptime = datetime.now(UTC)

        self.bot: Bot = Bot(self.config.bot_token)
        self.dp = Dispatcher()
        self.waiter = EventWaiter()
        self.db = Database(
            self.config.database_url,
            pool_size=self.config.db_pool_size,
            max_overflow=self.config.db_max_overflow,
            pool_recycle=self.config.db_pool_recycle,
        )
        self.http_session = aiohttp.ClientSession()

        self.commands = load_instances_from_directory("commands", "commands", BaseCommand, self)
        self.buttons = load_instances_from_directory("buttons", "buttons", BaseButton, self)
        self.messages = load_instances_from_directory("messages", "messages", BaseMessage, self)
        self.schedules = load_instances_from_directory("schedules", "schedules", BaseSchedule, self)

    def setup_handlers(self) -> None:
        self.logger.info("Loading existing handlers:")

        count = 0
        for command in self.commands:
            self.dp.message.register(command.handle, Command(command.name))

            count += 1
            self.logger.info("[command] Loaded /%s - %s", command.name, command.description)
        self.logger.info("Loaded %d commands", count)

        count = 0
        for button in self.buttons:
            self.dp.callback_query.register(button.handle, F.data == button.callback_data)

            count += 1
            self.logger.info("[button] Loaded handler: %s", button.callback_data)
        self.logger.info("Loaded %d buttons", count)

        count = 0
        for message in self.messages:
            route_filter = message.route_filter()
            if route_filter is None:
                self.dp.message.register(message.handle)
            else:
                self.dp.message.register(message.handle, route_filter)

            count += 1
            self.logger.info("[message trigger] Loaded trigger: %s", message.trigger)
        self.logger.info("Loaded %d message triggers", count)

        self.dp.message.register(self._handle_message_waiter)
        self.dp.callback_query.register(self._handle_button_waiter)

    async def _handle_message_waiter(self, message: Message) -> None:
        await self.waiter.resolve_message(message)

    async def _handle_button_waiter(self, callback: CallbackQuery) -> None:
        await self.waiter.resolve_button(callback)

    async def wait_for_message(self, chat_id: int, user_id: int, timeout: int, on_timeout=None):
        return await self.waiter.wait_message(chat_id, user_id, timeout, on_timeout)

    async def wait_for_button(
        self,
        chat_id: int,
        user_id: int,
        timeout: int,
        message_id: int | None = None,
        on_timeout=None,
    ):
        return await self.waiter.wait_button(chat_id, user_id, timeout, message_id, on_timeout)

    async def start_schedules(self) -> None:
        count = 0

        for schedule in self.schedules:
            asyncio.create_task(schedule.run_forever())

            count += 1
            self.logger.info("[schedule] Loaded %s every %s seconds", schedule.__class__.__name__, schedule.delay_seconds)

        self.logger.info("Loaded %d schedules", count)

    async def run(self) -> None:
        self.setup_handlers()
        await self.start_schedules()
        await self.dp.start_polling(self.bot)

    async def shutdown(self) -> None:
        await self.db.dispose()
        await self.http_session.close()
        await self.bot.session.close()
        self.logger.info("Bot shutdown complete")
