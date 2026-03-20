from sqlalchemy import String, VARCHAR, Boolean
from sqlalchemy.orm import mapped_column

from core.database.base import BaseEntity


class StreamTopicEntity(BaseEntity):
    __tablename__ = "stream_topics"

    name = mapped_column(VARCHAR(255), nullable=False)
    triggers = mapped_column(String, nullable=True)
    enabled = mapped_column(Boolean, nullable=False, default=True)
    is_youtube = mapped_column(Boolean, nullable=False, default=False)
    is_twitch = mapped_column(Boolean, nullable=False, default=False)
