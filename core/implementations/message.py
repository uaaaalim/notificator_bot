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

    async def execute(self, message: Message) -> None:
        raise NotImplementedError
