from enum import Enum
from typing import TYPE_CHECKING

from aiogram.types import Message

if TYPE_CHECKING:
    from core.client import BotClient


class CommandPermissionLevel(Enum):
    DEFAULT = 0
    OWNER = 1


class BaseCommand:
    name = ""
    description = ""
    permission_level = CommandPermissionLevel.DEFAULT
    is_visible = True

    def __init__(self, client: "BotClient") -> None:
        self.client = client

    async def handle(self, message: Message) -> None:
        if not message.from_user:
            self.client.logger.warning("Command /%s skipped: no from_user", self.name)
            return
        if self.client.waiter.is_waiting_any(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        ):
            return

        if self.permission_level == CommandPermissionLevel.OWNER:
            if message.from_user.id not in self.client.config.owner_ids:
                await message.reply(
                    text="❌ У вас нет доступа к данной команде!\n"
                         f"Доступ только для пользователей уровня: {CommandPermissionLevel.OWNER.name}",
                    parse_mode="HTML"
                )
                return

        await self.execute(message)

    async def execute(self, message: Message) -> None:
        raise NotImplementedError
