from functools import wraps
from datetime import datetime, UTC
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from src.models.enum import ModelType
from src.models.database import SettingValueType, SettingScope, SettingKey
from src.models.database import Conversation, Message, Setting
from src.models.decorators import validate_db_model

class ConversationDTO(BaseModel):
    id: Optional[int] = None
    title: str
    model_type: ModelType
    model_name: str
    system_prompt: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_db_model(cls, conversation: Conversation) -> "ConversationDTO":
        return cls(
            id=conversation.id,
            title=conversation.title,
            model_type=conversation.model_type,
            model_name=conversation.model_name,
            system_prompt=conversation.system_prompt,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    @validate_db_model
    def to_db_model(self) -> Conversation:
        return Conversation(
            title=self.title,
            model_type=self.model_type,
            model_name=self.model_name,
            system_prompt=self.system_prompt,
            created_at=self.created_at or datetime.now(UTC),
            updated_at=self.updated_at or datetime.now(UTC)
        )

class MessageDTO(BaseModel):
    id: Optional[int] = None
    conversation_id: Optional[int] = None
    role: str
    content: str
    created_at: Optional[datetime] = None
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

    @validate_db_model
    def to_db_model(self) -> Message:
        return Message(
            conversation_id=self.conversation_id,
            role=self.role,
            content=self.content.strip(),
            created_at=self.created_at or datetime.now(UTC),
            generation_info=self.generation_info
        )

class SettingDTO(BaseModel):
    id: Optional[int] = None
    key: SettingKey
    value: Any
    value_type: SettingValueType
    scope: SettingScope
    scope_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_model(cls, setting: Setting) -> "SettingDTO":
        return cls(
            id=setting.id,
            key=setting.key,
            value=setting.value,
            value_type=setting.value_type,
            scope=setting.scope,
            scope_id=setting.scope_id,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )

    @validate_db_model
    def to_db_model(self) -> Setting:
        return Setting(
            key=self.key.strip(),
            value=str(self.value),
            value_type=self.value_type,
            scope=self.scope,
            scope_id=self.scope_id,
            created_at=self.created_at or datetime.now(UTC),
            updated_at=self.updated_at or datetime.now(UTC)
        ) 