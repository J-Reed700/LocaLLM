from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, inspect
from sqlalchemy.orm import selectinload
from src.models.database import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: T):
        self.session = session
        self.model = model

    async def add(self, obj: T) -> T:
        try:
            # Check if object already exists in session
            if inspect(obj).persistent:
                return await self.update(obj)
            
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except Exception as e:
            await self.session.rollback()
            raise

    async def get(self, obj_id: int) -> Optional[T]:
        return await self.session.get(self.model, obj_id)

    async def list(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def delete(self, obj: T) -> None:
        try:
            await self.session.delete(obj)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise

    async def update(self, obj: T) -> T:
        try:
            # Merge the object to handle detached instances
            obj = await self.session.merge(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except Exception as e:
            await self.session.rollback()
            raise