from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.config import ConfigEntity


async def get_config(session: AsyncSession, name: str, default: Optional[str] = None) -> Optional[str]:
    entity = await session.scalar(
        select(ConfigEntity).where(ConfigEntity.name == name)
    )

    if entity is None:
        return default

    return entity.value


async def get_config_entity(session: AsyncSession, name: str) -> Optional[ConfigEntity]:
    return await session.scalar(
        select(ConfigEntity).where(ConfigEntity.name == name)
    )


async def get_configs(session: AsyncSession) -> list[ConfigEntity]:
    result = await session.scalars(select(ConfigEntity))
    return list(result.all())


async def set_config(
    session: AsyncSession,
    name: str,
    value: str,
    data: Optional[str] = None,
) -> ConfigEntity:
    entity = await session.scalar(
        select(ConfigEntity).where(ConfigEntity.name == name)
    )

    if entity is None:
        entity = ConfigEntity(
            name=name,
            value=value,
            data=data,
        )
        session.add(entity)
    else:
        entity.value = value
        entity.data = data

    await session.flush()
    return entity


async def delete_config(session: AsyncSession, name: str) -> bool:
    entity = await session.scalar(
        select(ConfigEntity).where(ConfigEntity.name == name)
    )

    if entity is None:
        return False

    await session.delete(entity)
    await session.flush()
    return True