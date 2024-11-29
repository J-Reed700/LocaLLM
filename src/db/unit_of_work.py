from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Any, Callable, Optional, Type
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import Select
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

T = TypeVar('T')

class UnitOfWork:
    def __init__(self, session: AsyncSession, max_retries: int = 3, retry_delay: float = 0.1):
        self._session = session
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(Exception)
    )
    async def add(self, obj) -> Any:
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def add_with_retry(self, obj) -> Any:
        return await self.add(obj)

    async def get(self, model_class: Type[T], id: Any) -> Optional[T]:
        return await self._session.get(model_class, id)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(Exception)
    )
    async def get_with_retry(self, model_class: Type[T], id: Any) -> Optional[T]:
        return await self.get(model_class, id)

    async def delete(self, obj) -> None:
        await self._session.delete(obj)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(Exception)
    )
    async def delete_with_retry(self, obj) -> None:
        await self.delete(obj)

    async def commit(self) -> None:
        await self._session.commit()

    @retry(
        stop=stop_after_attempt(1),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(Exception)
    )
    async def commit_with_retry(self) -> None:
        await self.commit()
        
    @asynccontextmanager
    async def transaction(self):
        try:
            yield self
            await self.commit()
        except Exception as e:
            await self.rollback()
            raise e

    @asynccontextmanager
    async def transaction_with_retry(self):
        try:
            yield self
            await self.commit_with_retry()
        except Exception as e:
            await self.rollback()
            raise e

    async def rollback(self):
        await self._session.rollback()

    async def flush(self):
        await self._session.flush()

    async def execute(self, query: Select) -> Any:
        return await self._session.execute(query)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(Exception)
    )
    async def execute_with_retry(self, query: Select) -> Any:
        return await self.execute(query)

    async def refresh(self, obj: Any) -> None:
        await self._session.refresh(obj)

    async def close(self):
        await self._session.close()