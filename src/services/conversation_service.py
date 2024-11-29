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
            model_type=data.type,
            model_name=data.name
        )
        saved = await self.db_context.conversations.save_with_retry(conversation)
        if not saved or not saved.id:
            raise ValueError("Failed to create conversation: Database did not return ID")
        return ConversationDTO.from_db_model(saved)
    
    async def update(self, id: int, data: ConversationUpdate) -> ConversationDTO:
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found")
        
        conversation.title = data.title
        conversation.updated_at = datetime.now(timezone.utc)
        
        updated = await self.db_context.conversations.update_with_retry(conversation)
        if not updated or not updated.id:
            raise ValueError("Failed to update conversation: Database did not return ID")
        return ConversationDTO.from_db_model(updated)
    
    async def get(self, id: int) -> Optional[ConversationDTO]:
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found")
        return ConversationDTO.from_db_model(conversation)
    
    async def list(self) -> List[ConversationDTO]:
        conversations = await self.db_context.conversations.list_all()
        return [ConversationDTO.from_db_model(conv) for conv in conversations]
    
    async def delete(self, id: int):
        conversation = await self.db_context.conversations.get_by_id(id)
        if not conversation:
            raise NotFoundError(f"Conversation {id} not found")
        await self.db_context.conversations.delete_by_id_with_retry(id)