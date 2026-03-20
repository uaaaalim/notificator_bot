from sqlalchemy.ext.asyncio import AsyncSession

from core.database.crud import CRUDRepository
from database.entities.stream_topic import StreamTopicEntity


class StreamTopicsRepository(CRUDRepository[StreamTopicEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(StreamTopicEntity, session)
