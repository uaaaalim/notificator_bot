from sqlalchemy import Column, BigInteger

from core.database.base import BaseEntity


class SubscriberEntity(BaseEntity):
    __tablename__ = "subscribers"

    tg_id = Column(BigInteger, nullable=False)
    # topic
