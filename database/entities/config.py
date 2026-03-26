from sqlalchemy import String, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import BaseEntity


class ConfigEntity(BaseEntity):
    __tablename__ = "configs"

    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    value: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    data: Mapped[str] = mapped_column(String, nullable=True)
