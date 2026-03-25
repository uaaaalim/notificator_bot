from sqlalchemy import Boolean, String, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.base import BaseEntity
from database.entities.subscribers import subscriber_stream_topics


class StreamTopicEntity(BaseEntity):
    __tablename__ = "stream_topics"

    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    triggers: Mapped[str | None] = mapped_column(String, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_youtube: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_twitch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    is_night: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    subscribers: Mapped[list["SubscriberEntity"]] = relationship(
        secondary=subscriber_stream_topics,
        back_populates="stream_topics",
        lazy="raise",
    )
