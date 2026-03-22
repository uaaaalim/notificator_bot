from sqlalchemy import BigInteger, Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.base import Base
from core.database.base import BaseEntity


subscriber_stream_topics = Table(
    "subscriber_stream_topics",
    Base.metadata,
    Column(
        "subscriber_id",
        BigInteger,
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "stream_topic_id",
        BigInteger,
        ForeignKey("stream_topics.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class SubscriberEntity(BaseEntity):
    __tablename__ = "subscribers"

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    stream_topics: Mapped[list["StreamTopicEntity"]] = relationship(
        secondary=subscriber_stream_topics,
        back_populates="subscribers",
        lazy="raise",
    )
