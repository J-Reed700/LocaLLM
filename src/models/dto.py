from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, List
from src.models.enum import ModelType
from src.models.database import Conversation, Message

class ConversationDTO(BaseModel):
    id: int
    title: str
    model_type: ModelType
    model_name: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_db_model(cls, conversation: Conversation) -> "ConversationDTO":
        return cls(
            id=conversation.id,
            title=conversation.title,
            model_type=conversation.model_type,
            model_name=conversation.model_name,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    def to_db_model(self) -> Conversation:
        return Conversation(
            id=self.id,
            title=self.title,
            model_type=self.model_type,
            model_name=self.model_name
        )

class MessageDTO(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    generation_info: Optional[Dict] = None
    
    @classmethod
    def from_db_model(cls, message: Message) -> "MessageDTO":
        return cls(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            generation_info=message.generation_info
        ) 