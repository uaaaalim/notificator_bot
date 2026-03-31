import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.client import BotClient


class ScheduleStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERRORED = "ERRORED"
    FINISHED = "FINISHED"


class BaseSchedule:
    delay_seconds = 60
    max_retries = 3

    def __init__(self, client: "BotClient") -> None:
        self.client: "BotClient" = client
        self.status = ScheduleStatus.IDLE
        self.error: str | None = None
        self.last_run_at: datetime | None = None

    async def run_forever(self) -> None:
        while True:
            await asyncio.sleep(self.delay_seconds)
            await self.run_once()

    async def run_once(self) -> None:
        self.last_run_at = datetime.now(timezone.utc)
        self.status = ScheduleStatus.RUNNING
        retry = 0
        while retry <= self.max_retries:
            try:
                await self.execute()
                self.status = ScheduleStatus.FINISHED
                self.error = None
                return
            except Exception as exc:  # noqa: BLE001
                retry += 1
                self.status = ScheduleStatus.ERRORED
                self.error = str(exc)

                self.client.logger.error(
                    f"[schedule] An error occurred in {self.__class__.__name__}:",
                    exc
                )

                if retry > self.max_retries:
                    return

    async def execute(self) -> None:
        raise NotImplementedError
