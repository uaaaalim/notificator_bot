from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import tomllib
from aiogram.enums import ParseMode
from aiogram.types import Message

from core.implementations.command import BaseCommand, CommandPermissionLevel


class StatusCommand(BaseCommand):
    name = "status"
    description = "Статус бота и расписаний"
    permission_level = CommandPermissionLevel.OWNER

    async def execute(self, message: Message) -> None:
        project_name, project_version = self._get_project_meta()
        commit_hash = self._get_last_commit_hash()
        memory_usage = self._get_memory_usage()

        lines = [
            "📊 <b>Статус бота</b>",
            "",
            f"🧩 Проект: <code>{project_name}</code>",
            f"🏷️ Версия: <code>{project_version}</code>",
            f"🧬 Последний коммит: <code>{commit_hash}</code>",
            f"🧠 Потребление ОЗУ: <code>{memory_usage}</code>",
            "",
            "🕒 <b>Schedules</b>",
        ]

        if not self.client.schedules:
            lines.append("— Нет загруженных schedules")
        else:
            now = datetime.now(timezone.utc)
            for schedule in self.client.schedules:
                last_run_at: datetime | None = getattr(schedule, "last_run_at", None)
                if last_run_at is None:
                    last_run_text = "никогда"
                else:
                    delta_seconds = max(0, int((now - last_run_at).total_seconds()))
                    last_run_text = f"{self._format_interval(delta_seconds)} назад"

                lines.append(
                    (
                        f"• <b>{schedule.__class__.__name__}</b>"
                        f" | статус: <code>{schedule.status.value}</code>"
                        f" | интервал: <code>{self._format_interval(schedule.delay_seconds)}</code>"
                        f" | последний запуск: <code>{last_run_text}</code>"
                    )
                )

        await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)

    @staticmethod
    def _get_project_meta() -> tuple[str, str]:
        default_name = "unknown"
        default_version = "unknown"

        try:
            repo_root = Path(__file__).resolve().parents[1]
            pyproject_path = repo_root / "pyproject.toml"
            with pyproject_path.open("rb") as file:
                pyproject_data = tomllib.load(file)

            project_data = pyproject_data.get("project", {})
            name = project_data.get("name", default_name)
            version = project_data.get("version", default_version)
            return str(name), str(version)
        except Exception:
            return default_name, default_version

    @staticmethod
    def _get_last_commit_hash() -> str:
        try:
            repo_root = Path(__file__).resolve().parents[1]
            result = subprocess.check_output(
                ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
                text=True,
            )
            return result.strip() or "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def _get_memory_usage() -> str:
        status_path = Path("/proc/self/status")
        try:
            with status_path.open("r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith("VmRSS:"):
                        kb_value = int(line.split()[1])
                        mb_value = kb_value / 1024
                        return f"{mb_value:.2f} MB"
        except Exception:
            pass

        return "unknown"

    @staticmethod
    def _format_interval(seconds: int) -> str:
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}ч. {minutes}мин. {secs}сек."
