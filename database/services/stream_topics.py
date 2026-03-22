from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.stream_topic import StreamTopicEntity


async def get_stream_topics(session: AsyncSession) -> Sequence[StreamTopicEntity]:
    result = await session.scalars(select(StreamTopicEntity))
    return result.all()


async def create_stream_topic(
    session: AsyncSession,
    *,
    name: str,
    triggers: str | None = None,
    enabled: bool = True,
    is_youtube: bool = False,
    is_twitch: bool = False,
) -> StreamTopicEntity:
    topic = StreamTopicEntity(
        name=name,
        triggers=triggers,
        enabled=enabled,
        is_youtube=is_youtube,
        is_twitch=is_twitch,
    )
    session.add(topic)
    await session.flush()
    return topic


async def delete_stream_topic_by_id(session: AsyncSession, topic_id: int) -> bool:
    topic = await session.get(StreamTopicEntity, topic_id)
    if not topic:
        return False

    await session.delete(topic)
    await session.flush()
    return True
