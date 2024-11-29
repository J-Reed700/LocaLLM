from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.db.unit_of_work import UnitOfWork

class DatabaseContext:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        
    async def __aenter__(self) -> 'DatabaseContext':
        if not self._session:
            session = self._session_factory()
            self._session = await session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            if exc_type:
                await self._session.rollback()
            else:
                await self._session.commit()
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    @property
    def session(self) -> AsyncSession:
        if not self._session:
            self._session = self._session_factory()
        return self._session

    @property
    def uow(self) -> UnitOfWork:
        return UnitOfWork(self.session)
    
    @property
    def conversations(self) -> ConversationRepository:
        return ConversationRepository(self.uow)
        
    @property
    def messages(self) -> MessageRepository:
        return MessageRepository(self.uow)        
    
    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
        