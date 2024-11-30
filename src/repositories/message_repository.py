from src.repositories.base_repository import BaseRepository, transaction
from src.models.database import Message, MessageRoleEnum
from src.db.unit_of_work import UnitOfWork
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone

class MessageRepository(BaseRepository[Message]):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, Message)
    
    async def get_conversation_messages(self, conversation_id: int, before_message_id: Optional[int] = None) -> List[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id)
        if before_message_id:
            query = query.where(Message.id < before_message_id)
        result = await self.execute(query)
        return result.scalars().all()

    async def create_message(self, conversation_id: int, role: MessageRoleEnum, content: str, generation_info: dict = None) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            generation_info=generation_info
        )
        self._set_timestamps(message)
        return await self.add_with_retry(message)
    


