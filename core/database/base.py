from sqlalchemy import BigInteger, Sequence
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


ID_SEQUENCE = Sequence("entity_id_seq", start=100000, increment=1)


class Base(DeclarativeBase):
    pass


class BaseEntity(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger,
        ID_SEQUENCE,
        primary_key=True,
        server_default=ID_SEQUENCE.next_value(),
    )
