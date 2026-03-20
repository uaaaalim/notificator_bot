import importlib
import os
import pkgutil
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from core.database.base import Base


def import_all_entities(package_name: str = "database.entities") -> None:
    package = importlib.import_module(package_name)

    if not hasattr(package, "__path__"):
        return

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if module_name.startswith("_") or is_pkg:
            continue
        importlib.import_module(f"{package_name}.{module_name}")


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

import_all_entities()
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
