from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from websrc.models.database import User, Conversation, Message
from websrc.config.logging_config import LoggerMixin, log_async_function
from websrc.models.pydantic import ModelType

class DatabaseService(LoggerMixin):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = self.logger

    @log_async_function
    async def create_user(self, username: str) -> User:
        user = User(username=username)
        self.session.add(user)
        await self.session.commit()
        return user

    @log_async_function
    async def get_user_conversations(self, user_id: int) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        return result.scalars().all()

    @log_async_function
    async def create_conversation(
        self, 
        user_id: int, 
        title: str,
        model_type: ModelType,
        model_name: str
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title,
            model_type=model_type,
            model_name=model_name
        )
        self.session.add(conversation)
        await self.session.commit()
        return conversation

    @log_async_function
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )
        self.session.add(message)
        await self.session.commit()
        return message
