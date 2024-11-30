from typing import Generic, TypeVar, Optional, List, Type, Callable, Any
from sqlalchemy import select
from datetime import datetime, timezone
from src.models.database import Base
from src.db.unit_of_work import UnitOfWork
from functools import wraps

T = TypeVar('T', bound=Base)

def transaction(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self: 'BaseRepository', *args, **kwargs):
        async with self.uow.transaction():
            return await func(self, *args, **kwargs)
    return wrapper

def transaction_with_retry(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self: 'BaseRepository', *args, **kwargs):
        async with self.uow.transaction_with_retry():
            return await func(self, *args, **kwargs)
    return wrapper

class BaseRepository(Generic[T]):
    def __init__(self, unit_of_work: UnitOfWork, model_class: Type[T]):
        self.uow = unit_of_work
        self.model_class = model_class

    def _set_timestamps(self, entity: T) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if hasattr(entity, 'created_at') and entity.created_at is None:
            entity.created_at = now
        if hasattr(entity, 'updated_at'):
            entity.updated_at = now

    async def list(self) -> List[T]:
        """List all entities of type T"""
        query = select(self.model_class)
        result = await self.uow.execute(query)
        return list(result.scalars().all())

    @transaction
    async def save(self, entity: T) -> T:
        self._set_timestamps(entity)
        await self.uow.add(entity)
        await self.uow.flush()
        return entity

    @transaction_with_retry
    async def save_with_retry(self, entity: T) -> T:
        self._set_timestamps(entity)
        await self.uow.add_with_retry(entity)
        await self.uow.flush()
        return entity

    async def get(self, id: int) -> Optional[T]:
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.uow.execute(query)
        return result.scalar_one_or_none()

    @transaction
    async def delete(self, entity: T) -> None:
        await self.uow.delete(entity)

    @transaction_with_retry
    async def delete_with_retry(self, entity: T) -> None:
        await self.uow.delete_with_retry(entity)
    
    