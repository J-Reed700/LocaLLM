from typing import List, Optional
from src.models.database import Conversation
from src.models.dto import ConversationDTO
from src.models.pydantic import ConversationCreate, ConversationUpdate
from src.services.database_context import DatabaseContext
from exceptions.exceptions import NotFoundError
from datetime import datetime, timezone

class ConversationService:
    def __init__(self, db_context: DatabaseContext):
        self.db_context = db_context
    
    async def create(self, data: ConversationCreate) -> ConversationDTO:
        conversation = Conversation(
            title=data.title,
            model_type=data.parameters.type,
            model_name=data.parameters.name,
            system_prompt=data.system_prompt
        )
        saved = await self.db_context.conversations.add_with_retry(conversation)
        if not saved or not saved.id:
            raise ValueError("Failed to create conversation: Database did not return ID")
        return ConversationDTO.from_db_model(saved)
    
    async def update(self, id: int, data: ConversationUpdate) -> ConversationDTO:
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found", source_class=self.__class__.__name__)
        
        conversation.title = data.title
        conversation.system_prompt = data.system_prompt
        
        updated = await self.db_context.conversations.update_with_retry(conversation)
        if not updated or not updated.id:
            raise ValueError("Failed to update conversation: Database did not return ID")
        return ConversationDTO.from_db_model(updated)
    
    async def get(self, id: int) -> Optional[ConversationDTO]:
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found", source_class=self.__class__.__name__)
        return ConversationDTO.from_db_model(conversation)
    
    async def list(self, order_by: str = "created_at", order_direction: str = "asc") -> List[ConversationDTO]:
        conversations = await self.db_context.conversations.list_all(order_by, order_direction)
        return [ConversationDTO.from_db_model(conv) for conv in conversations]
    
    async def delete_by_id(self, id: int):
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found", source_class=self.__class__.__name__)
        await self.db_context.conversations.delete(conversation)