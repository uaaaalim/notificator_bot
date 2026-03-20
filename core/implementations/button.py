from typing import TYPE_CHECKING

from aiogram.types import CallbackQuery

if TYPE_CHECKING:
    from core.client import BotClient


class BaseButton:
    callback_data = ""

    def __init__(self, client: "BotClient") -> None:
        self.client = client

    async def handle(self, callback: CallbackQuery) -> None:
        if not callback.from_user:
            self.client.logger.warning("button %s skipped: no from_user", self.callback_data)
            return

        if callback.message and self.client.waiter.is_waiting_any(
                chat_id=callback.message.chat.id,
                user_id=callback.from_user.id,
        ):
            await callback.answer(
                "Есть активное незавершённое действие. Сейчас нажимать кнопки нельзя.",
                show_alert=True,
            )
            return

        await self.execute(callback)

    async def execute(self, callback: CallbackQuery) -> None:
        raise NotImplementedError
