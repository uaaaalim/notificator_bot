from sqlalchemy.ext.asyncio import AsyncSession

from core.database.crud import CRUDRepository
from database.entities.subscribers import SubscriberEntity


class SubscribersRepository(CRUDRepository[SubscriberEntity]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SubscriberEntity, session)
