import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiogram.types import CallbackQuery, Message


@dataclass
class WaitContext:
    future: asyncio.Future[Any]
    timeout_task: asyncio.Task[None]


class EventWaiter:
    def __init__(self) -> None:
        self._message_waiters: dict[tuple[int, int], WaitContext] = {}
        self._button_waiters: dict[tuple[int, int, int], WaitContext] = {}

    async def wait_message(
        self,
        chat_id: int,
        user_id: int,
        timeout: int,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> Message | None:
        self._cancel_user_waits(chat_id, user_id)
        key = (chat_id, user_id)
        future: asyncio.Future[Message] = asyncio.get_running_loop().create_future()
        timeout_task = asyncio.create_task(self._on_timeout(self._message_waiters, key, timeout, on_timeout))
        self._message_waiters[key] = WaitContext(future=future, timeout_task=timeout_task)
        return await future

    async def wait_button(
        self,
        chat_id: int,
        user_id: int,
        timeout: int,
        message_id: int | None = None,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> CallbackQuery | None:
        self._cancel_user_waits(chat_id, user_id)
        key = (chat_id, user_id, message_id if message_id is not None else -1)
        future: asyncio.Future[CallbackQuery] = asyncio.get_running_loop().create_future()
        timeout_task = asyncio.create_task(self._on_timeout(self._button_waiters, key, timeout, on_timeout))
        self._button_waiters[key] = WaitContext(future=future, timeout_task=timeout_task)
        return await future

    async def resolve_message(self, message: Message) -> bool:
        key = (message.chat.id, message.from_user.id)
        ctx = self._message_waiters.pop(key, None)
        if not ctx:
            return False

        ctx.timeout_task.cancel()
        if not ctx.future.done():
            ctx.future.set_result(message)
        return True

    async def resolve_button(self, callback: CallbackQuery) -> bool:
        if not callback.message:
            return False

        scoped_key = (callback.message.chat.id, callback.from_user.id, callback.message.message_id)
        common_key = (callback.message.chat.id, callback.from_user.id, -1)
        ctx = self._button_waiters.pop(scoped_key, None)
        if not ctx:
            ctx = self._button_waiters.pop(common_key, None)
        if not ctx:
            return False

        ctx.timeout_task.cancel()
        if not ctx.future.done():
            ctx.future.set_result(callback)
        return True

    def is_waiting_button(self, chat_id: int, user_id: int) -> bool:
        for wait_chat_id, wait_user_id, _ in self._button_waiters:
            if wait_chat_id == chat_id and wait_user_id == user_id:
                return True
        return False

    def is_waiting_message(self, chat_id: int, user_id: int) -> bool:
        return (chat_id, user_id) in self._message_waiters

    def is_waiting_any(self, chat_id: int, user_id: int) -> bool:
        return self.is_waiting_message(chat_id, user_id) or self.is_waiting_button(chat_id, user_id)

    def _cancel_user_waits(self, chat_id: int, user_id: int) -> None:
        message_ctx = self._message_waiters.pop((chat_id, user_id), None)
        if message_ctx:
            message_ctx.timeout_task.cancel()
            if not message_ctx.future.done():
                message_ctx.future.set_result(None)

        button_keys = [
            key for key in self._button_waiters
            if key[0] == chat_id and key[1] == user_id
        ]
        for key in button_keys:
            button_ctx = self._button_waiters.pop(key, None)
            if not button_ctx:
                continue
            button_ctx.timeout_task.cancel()
            if not button_ctx.future.done():
                button_ctx.future.set_result(None)

    async def _on_timeout(
        self,
        store: dict[tuple[int, ...], WaitContext],
        key: tuple[int, ...],
        timeout: int,
        on_timeout: Callable[[], Awaitable[None]] | None,
    ) -> None:
        await asyncio.sleep(timeout)
        ctx = store.pop(key, None)
        if not ctx:
            return

        if on_timeout:
            await on_timeout()
        if not ctx.future.done():
            ctx.future.set_result(None)
