from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.entities.stream_topic import StreamTopicEntity


async def get_stream_topics(session: AsyncSession) -> Sequence[StreamTopicEntity]:
    result = await session.scalars(select(StreamTopicEntity))
    return result.all()
