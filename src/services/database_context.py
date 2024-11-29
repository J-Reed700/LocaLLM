from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.db.unit_of_work import UnitOfWork
from src.db.session import AsyncSessionLocal

class DatabaseContext:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        
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

    async def __aenter__(self) -> 'DatabaseContext':
        return self
        