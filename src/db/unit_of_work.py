from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Any, Callable, Optional, Type
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import Select
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from exceptions.exceptions import DatabaseError

T = TypeVar('T')

class UnitOfWork:
    def __init__(self, session: AsyncSession, max_retries: int = 3, retry_delay: float = 0.1):
        self._session = session
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def add(self, obj) -> Any:
        try:
            self._session.add(obj)
            await self._session.flush()
            await self._session.refresh(obj)
            return obj
        except Exception as e:
            raise DatabaseError(f"Failed to add object: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(DatabaseError)
    )
    async def add_with_retry(self, obj) -> Any:
        try:
            return await self.add(obj)
        except Exception as e:
            raise DatabaseError(f"Failed to add object after retries: {str(e)}")
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(DatabaseError)
    )
    async def delete_with_retry(self, obj) -> None:
        try:
            await self.delete(obj)
        except Exception as e:
            raise DatabaseError(f"Failed to delete object after retries: {str(e)}")

    async def delete(self, obj) -> None:
        try:
            await self._session.delete(obj)
        except Exception as e:
            raise DatabaseError(f"Failed to delete object: {str(e)}")
        
    async def commit(self) -> None:
        try:
            await self._session.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to commit transaction: {str(e)}")

    @retry(
        stop=stop_after_attempt(1),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(DatabaseError)
    )
    async def commit_with_retry(self) -> None:
        try:
            await self.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to commit transaction after retry: {str(e)}")
        
    @asynccontextmanager
    async def transaction(self):
        try:
            yield self
            await self.commit()
        except Exception as e:
            await self.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")

    @asynccontextmanager
    async def transaction_with_retry(self):
        try:
            yield self
            await self.commit_with_retry()
        except Exception as e:
            await self.rollback()
            raise DatabaseError(f"Transaction with retry failed: {str(e)}")

    async def rollback(self):
        try:
            await self._session.rollback()
        except Exception as e:
            raise DatabaseError(f"Failed to rollback transaction: {str(e)}")

    async def flush(self):
        try:
            await self._session.flush()
        except Exception as e:
            raise DatabaseError(f"Failed to flush session: {str(e)}")

    async def execute(self, query: Select) -> Any:
        try:
            return await self._session.execute(query)
        except Exception as e:
            raise DatabaseError(f"Failed to execute query: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1),
        retry=retry_if_exception_type(DatabaseError)
    )
    async def execute_with_retry(self, query: Select) -> Any:
        try:
            return await self.execute(query)
        except Exception as e:
            raise DatabaseError(f"Failed to execute query after retries: {str(e)}")

    async def refresh(self, obj: Any) -> None:
        try:
            await self._session.refresh(obj)
        except Exception as e:
            raise DatabaseError(f"Failed to refresh object: {str(e)}")

    async def close(self):
        try:
            await self._session.close()
        except Exception as e:
            raise DatabaseError(f"Failed to close session: {str(e)}")