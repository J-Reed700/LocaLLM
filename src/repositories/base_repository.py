from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy import select
from datetime import datetime, timezone
from src.models.database import Base
from src.db.unit_of_work import UnitOfWork

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, unit_of_work: UnitOfWork, model_class: Type[T]):
        self.uow = unit_of_work
        self.model_class = model_class

    async def list(self) -> List[T]:
        """List all entities of type T"""
        query = select(self.model_class)
        result = await self.uow.execute(query)
        return list(result.scalars().all())

    async def save(self, entity: T) -> T:
        async with self.uow.transaction():
            return await self.add(entity)

    async def add(self, entity: T) -> T:
        if hasattr(entity, 'created_at'):
            if entity.created_at is None:
                entity.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            naive_dt = entity.created_at.astimezone(timezone.utc).replace(tzinfo=None)
            entity.created_at = naive_dt
        if hasattr(entity, 'updated_at'):
            if entity.updated_at is None:
                entity.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            naive_dt = entity.updated_at.astimezone(timezone.utc).replace(tzinfo=None)
            entity.updated_at = naive_dt
            
        await self.uow.add(entity)
        await self.uow.flush()
        return entity

    async def save_with_retry(self, entity: T) -> T:
        async with self.uow.transaction_with_retry():
            return await self.add_with_retry(entity)

    async def add_with_retry(self, entity: T) -> T:
        if hasattr(entity, 'created_at'):
            if entity.created_at is None:
                entity.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            naive_dt = entity.created_at.astimezone(timezone.utc).replace(tzinfo=None)
            entity.created_at = naive_dt
            
        if hasattr(entity, 'updated_at'):
            if entity.updated_at is None:
                entity.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            naive_dt = entity.updated_at.astimezone(timezone.utc).replace(tzinfo=None)
            entity.updated_at = naive_dt
            
        await self.uow.add_with_retry(entity)
        await self.uow.flush()
        return entity

    async def get_by_id(self, id: int) -> Optional[T]:
        return await self.uow.get(self.model_class, id)

    async def list_all(self) -> List[T]:
        result = await self.uow.execute(select(self.model_class))
        return list(result.scalars().all())

    async def delete_by_id(self, id: int) -> None:
        async with self.uow.transaction():
            entity = await self.get_by_id(id)
            if entity:
                await self.delete(entity)

    async def delete(self, entity: T) -> None:
        await self.uow.delete(entity)

    async def delete_with_retry(self, entity: T) -> None:
        await self.uow.delete_with_retry(entity)

    async def get(self, id: int) -> Optional[T]:
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.uow.execute(query)
        return result.scalar_one_or_none()