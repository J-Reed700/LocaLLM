from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.models.database import (
    Category,
    Conversation,
    Message,
    FavoriteMessage, 
    FavoriteConversation
)
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.base_repository import BaseRepository
from websrc.config.logging_config import LoggerMixin, log_async_function
from sqlalchemy import select

class DatabaseService(LoggerMixin):
    def __init__(self, engine):
        self.engine = engine
        self.async_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        # Initialize repositories
        self._message_repo = None
        self._conversation_repo = None
        self._category_repo = None
        self._favorite_message_repo = None
        self._favorite_conversation_repo = None
        self._current_session = None

    async def get_session(self) -> AsyncSession:
        if not self._current_session:
            async with self.async_session() as session:
                self._current_session = session
                await session.begin()
        return self._current_session

    async def cleanup(self):
        if self._current_session:
            try:
                await self._current_session.close()
            finally:
                self._current_session = None

    @property
    async def message_repo(self) -> MessageRepository:
        if not self._message_repo:
            session = await self.get_session()
            self._message_repo = MessageRepository(session)
        return self._message_repo

    @property 
    async def conversation_repo(self) -> ConversationRepository:
        if not self._conversation_repo:
            session = await self.get_session()
            self._conversation_repo = ConversationRepository(session)
        return self._conversation_repo

    @property
    async def category_repo(self) -> BaseRepository[Category]:
        if not self._category_repo:
            session = await self.get_session()
            self._category_repo = BaseRepository(session, Category)
        return self._category_repo

    @property
    async def favorite_message_repo(self) -> BaseRepository[FavoriteMessage]:
        if not self._favorite_message_repo:
            session = await self.get_session()
            self._favorite_message_repo = BaseRepository(session, FavoriteMessage)
        return self._favorite_message_repo

    @property
    async def favorite_conversation_repo(self) -> BaseRepository[FavoriteConversation]:
        if not self._favorite_conversation_repo:
            session = await self.get_session()
            self._favorite_conversation_repo = BaseRepository(session, FavoriteConversation)
        return self._favorite_conversation_repo

    async def get_conversation_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        repo = await self.message_repo
        messages = await repo.get_conversation_messages(conversation_id)
        
        return [
            {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ]

    @log_async_function
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        generation_info: dict = None
    ) -> Message:
        """Add a new message to a conversation."""
        async with self.async_session() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                generation_info=generation_info
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    # Conversation CRUD operations
    @log_async_function
    async def create_conversation(self, title: str, model_type: str, model_name: str) -> Conversation:
        repo = await self.conversation_repo
        conversation = Conversation(
            title=title,
            model_type=model_type,
            model_name=model_name
        )
        return await repo.add(conversation)

    @log_async_function
    async def add_conversation(self, conversation: Conversation) -> Conversation:
        repo = await self.conversation_repo
        return await repo.add(conversation)

    @log_async_function
    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        repo = await self.conversation_repo
        return await repo.get(conversation_id)

    @log_async_function
    async def list_conversations(self) -> List[Conversation]:
        repo = await self.conversation_repo
        return await repo.list()

    @log_async_function
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        repo = await self.conversation_repo
        return await repo.update(conversation)

    @log_async_function
    async def delete_conversation(self, conversation: Conversation) -> None:
        repo = await self.conversation_repo
        await repo.delete(conversation)

    @log_async_function
    async def get_message(self, message_id: int) -> Optional[Message]:
        repo = await self.message_repo
        return await repo.get(message_id)

    @log_async_function
    async def list_messages(self) -> List[Message]:
        repo = await self.message_repo
        return await repo.list()

    @log_async_function
    async def update_message(self, message: Message) -> Message:
        repo = await self.message_repo
        return await repo.update(message)

    @log_async_function
    async def delete_message(self, message: Message) -> None:
        repo = await self.message_repo
        await repo.delete(message)
