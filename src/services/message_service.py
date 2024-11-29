from typing import List, Optional
from src.models.database import Message, MessageRoleEnum
from src.models.dto import MessageDTO
from src.models.pydantic import MessageCreate
from src.services.database_context import DatabaseContext
from exceptions.exceptions import NotFoundError

class MessageService:
    def __init__(self, db_context: DatabaseContext):
        self.db_context = db_context
    
    async def create(self, conversation_id: int, data: MessageCreate) -> MessageDTO:
        message = await self.db_context.messages.create_message_with_retry(
            conversation_id=conversation_id,
            role=data.role,
            content=data.content,
            generation_info=data.metadata
        )
        if not message or not message.id:
            raise ValueError("Failed to create message: Database did not return ID")
        return MessageDTO.from_db_model(message)
    
    async def get(self, id: int) -> Optional[MessageDTO]:
        message = await self.db_context.messages.get_by_id(id)
        if not message:
            return None
        return MessageDTO.from_db_model(message)
    
    async def list_by_conversation(self, conversation_id: int, before_message_id: Optional[int] = None) -> List[MessageDTO]:
        messages = await self.db_context.messages.get_conversation_messages(conversation_id, before_message_id)
        return [MessageDTO.from_db_model(msg) for msg in messages]
    
    async def delete(self, id: int) -> None:
        await self.db_context.messages.delete_by_id(id)