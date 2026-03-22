from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from database.entities.subscribers import SubscriberEntity


async def get_subscriber(
    session: AsyncSession,
    tg_id: int,
    *,
    options: Sequence[ORMOption] = (),
) -> SubscriberEntity | None:
    query = select(SubscriberEntity).where(SubscriberEntity.tg_id == tg_id)
    if options:
        query = query.options(*options)
    return await session.scalar(query)


async def ensure_subscriber(session: AsyncSession, tg_id: int) -> SubscriberEntity:
    stmt = (
        insert(SubscriberEntity)
        .values(tg_id=tg_id)
        .on_conflict_do_nothing(index_elements=[SubscriberEntity.tg_id])
    )
    await session.execute(stmt)

    subscriber = await get_subscriber(session, tg_id)
    if not subscriber:
        raise RuntimeError("Subscriber was not created or loaded")
    return subscriber
