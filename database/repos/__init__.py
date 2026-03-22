from sqlalchemy.ext.asyncio import AsyncSession

from database.repos.stream_topics import StreamTopicsRepository
from database.repos.subscribers import SubscribersRepository


class Repositories:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._subscribers = None
        self._stream_topics = None

    @property
    def subscribers(self) -> SubscribersRepository:
        if self._subscribers is None:
            self._subscribers = SubscribersRepository(self._session)
        return self._subscribers

    @property
    def stream_topics(self) -> StreamTopicsRepository:
        if self._stream_topics is None:
            self._stream_topics = StreamTopicsRepository(self._session)
        return self._stream_topics
