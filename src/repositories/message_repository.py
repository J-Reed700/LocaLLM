from src.repositories.base_repository import BaseRepository
from src.models.database import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_message(self, conversation_id: int, role: str, content: str, generation_info: dict = None) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            generation_info=generation_info
        )
        return await self.create(message)

    # Add message-specific manipulations here 