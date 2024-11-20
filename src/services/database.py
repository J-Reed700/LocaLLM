from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.database import User, Conversation, Message
from websrc.config.logging_config import LoggerMixin, log_async_function
from websrc.models.pydantic import ModelType

class DatabaseService(LoggerMixin):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        
    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            return session
            
    @log_async_function
    async def create_conversation(
        self,
        user_id: int,
        title: str,
        model_type: ModelType,
        model_name: str
    ) -> Conversation:
        async with await self.get_session() as session:
            conversation = Conversation(
                user_id=user_id,
                title=title,
                model_type=model_type,
                model_name=model_name
            )
            session.add(conversation)
            await session.commit()
            return conversation
            
    @log_async_function
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        async with await self.get_session() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata
            )
            session.add(message)
            await session.commit()
            return message
