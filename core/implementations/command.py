from typing import TYPE_CHECKING

from aiogram.types import Message

if TYPE_CHECKING:
    from core.client import BotClient


class BaseCommand:
    name = ""
    description = ""
    permission_level = 0
    is_visible = True

    def __init__(self, client: "BotClient") -> None:
        self.client = client

    async def handle(self, message: Message) -> None:
        if not message.from_user:
            # self.client.logger.warning("Command /%s skipped: no from_user", self.name)
            return
        if self.client.waiter.is_waiting_any(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        ):
            return
        await self.execute(message)

    async def execute(self, message: Message) -> None:
        raise NotImplementedError
