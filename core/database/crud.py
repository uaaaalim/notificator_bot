from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

ModelT = TypeVar("ModelT")


class CRUDRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get(self, entity_id: int) -> ModelT | None:
        query = select(self.model).where(self.model.id == entity_id)
        return await self.session.scalar(query)

    async def get_where(self, *conditions: ColumnElement[bool]) -> ModelT | None:
        query = select(self.model).where(*conditions)
        return await self.session.scalar(query)

    async def get_all(self) -> Sequence[ModelT]:
        query = select(self.model)
        result = await self.session.scalars(query)
        return result.all()

    async def update(self, new_obj: ModelT) -> ModelT:
        merged = await self.session.merge(new_obj)
        await self.session.commit()
        return merged

    async def update_where(self, entity_id: int, new_data: dict) -> None:
        stmt = update(self.model).where(self.model.id == entity_id).values(**new_data)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete(self, entity_id: int) -> None:
        stmt = delete(self.model).where(self.model.id == entity_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_where(self, *conditions: ColumnElement[bool]) -> None:
        stmt = delete(self.model).where(*conditions)
        await self.session.execute(stmt)
        await self.session.commit()
