from src.repositories.base_repository import BaseRepository
from src.models.database import Message, MessageRoleEnum
from src.db.unit_of_work import UnitOfWork
from sqlalchemy import select
from typing import List, Optional
from src.repositories.interfaces import IMessageRepository

class MessageRepository(BaseRepository[Message], IMessageRepository):
    def __init__(self, unit_of_work: UnitOfWork):
        self.uow = unit_of_work
        super().__init__(unit_of_work, Message)
    
    async def save(self, message: Message) -> Message:
        async with self.uow.transaction():
            return await self.add(message)
    
    async def get_by_id(self, id: int) -> Optional[Message]:
        return await self.get(id)
        
    async def list_all(self) -> List[Message]:
        return await self.list()
        
    async def delete_by_id(self, id: int) -> None:
        async with self.uow.transaction():
            message = await self.get_by_id(id)
            if message:
                await self.delete(message)
    
    async def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id)
        result = await self.uow.execute(query)
        return result.scalars().all()

    async def create_message(self, conversation_id: int, role: MessageRoleEnum, content: str, generation_info: dict = None) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            generation_info=generation_info
        )
        return await self.save(message)

    # Add message-specific manipulations here 