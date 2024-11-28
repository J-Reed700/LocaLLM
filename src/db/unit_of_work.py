from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type
from contextlib import asynccontextmanager

T = TypeVar('T')

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session
        
    async def add(self, obj) -> None:
        self._session.add(obj)
    
    async def delete(self, obj) -> None:
        await self._session.delete(obj)
        
    async def flush(self) -> None:
        await self._session.flush()
        
    async def refresh(self, obj) -> None:
        await self._session.refresh(obj)
        
    async def merge(self, obj):
        return await self._session.merge(obj)
        
    async def execute(self, query):
        return await self._session.execute(query)
        
    async def commit(self) -> None:
        try:
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e
            
    async def rollback(self) -> None:
        await self._session.rollback()
        
    @asynccontextmanager
    async def transaction(self):
        try:
            yield self
            await self.commit()
        except Exception as e:
            await self.rollback()
            raise e 