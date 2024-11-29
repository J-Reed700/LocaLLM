from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy import select
from src.models.database import Base
from src.db.unit_of_work import UnitOfWork

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, unit_of_work: UnitOfWork, model_class: Type[T]):
        self.uow = unit_of_work
        self.model_class = model_class

    async def add(self, obj: T) -> T:
        await self.uow.add(obj)
        await self.uow.flush()
        return obj

    async def get(self, id: int) -> Optional[T]:
        result = await self.uow.execute(
            select(self.model_class).filter(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self) -> List[T]:
        result = await self.uow.execute(select(self.model_class))
        return list(result.scalars().all())

    async def delete(self, obj: T) -> None:
        await self.uow.delete(obj)