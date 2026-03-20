from sqlalchemy.ext.asyncio import AsyncSession

from database.repos.stream_topics import StreamTopicsRepository
from database.repos.subscribers import SubscribersRepository


class Repositories:
    def __init__(self, session: AsyncSession) -> None:
        self.subscribers = SubscribersRepository(session)
        self.stream_topics = StreamTopicsRepository(session)
