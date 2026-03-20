import asyncio
import platform
import subprocess
import tomllib
from pathlib import Path

import aiogram
import alembic
import sqlalchemy
import asyncpg

from core.client import BotClient


def get_project_meta() -> dict[str, str]:
    pyproject_path = Path(__file__).resolve().parent / "pyproject.toml"

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        authors = project.get("authors", [])

        author_name = authors[0].get("name", "unknown") if authors else "unknown"
        author_email = authors[0].get("email", "unknown") if authors else "unknown"

        return {
            "name": project.get("name", "unknown"),
            "version": project.get("version", "unknown"),
            "author_name": author_name,
            "author_email": author_email,
        }
    except Exception:
        return {
            "name": "unknown",
            "version": "unknown",
            "author_name": "unknown",
            "author_email": "unknown",
        }


def get_git_short_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


async def main() -> None:
    meta = get_project_meta()
    client = BotClient()

    client.logger.info("Running project using utilities below:")
    client.logger.info("")
    client.logger.info("[entry] Project name: %s", meta["name"])
    client.logger.info("[entry] Version: %s", meta["version"])
    client.logger.info("[entry] Git commit: %s", get_git_short_hash())
    client.logger.info("[entry] Python version: %s", platform.python_version())
    client.logger.info("[entry] aiogram: %s", aiogram.__version__)
    client.logger.info("[entry] sqlalchemy: %s (with postgresql connection)", sqlalchemy.__version__)
    client.logger.info("[entry] asyncpg: %s", asyncpg.__version__)
    client.logger.info("[entry] alembic: %s", alembic.__version__)
    client.logger.info("")
    client.logger.info(
        "Welcome to %s, author: %s <%s>",
        meta["name"],
        meta["author_name"],
        meta["author_email"],
    )
    client.logger.info("Starting up...")

    await asyncio.sleep(0.7)

    try:
        await client.run()
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())