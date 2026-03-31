from typing import TYPE_CHECKING

from aiogram.types import Message

if TYPE_CHECKING:
    from core.client import BotClient


class BaseMessage:
    trigger = "*"

    def __init__(self, client: "BotClient") -> None:
        self.client = client

    async def handle(self, message: Message) -> None:
        if not message.from_user:
            self.client.logger.warning("message handler skipped: no from_user")
            return
        await self.execute(message)

    def route_filter(self):
        if self.trigger == "*":
            return None

        trigger = self.trigger.lower()

        def _filter(message: Message) -> bool:
            text = message.text or ""
            return text.lower().startswith(trigger)

        return _filter

    async def execute(self, message: Message) -> None:
        raise NotImplementedError
