from functools import wraps
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from src.models.enum import ModelType
from src.models.database import SettingValueType, SettingScope, SettingKey
from src.models.database import Conversation, Message, Setting
from src.models.decorators import validate_db_model
from src.models.database import ModelInfo
from huggingface_hub import ModelInfo as HFModelInfo
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
            created_at=self.created_at or datetime.now(timezone.utc),
            updated_at=self.updated_at or datetime.now(timezone.utc)
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
            created_at=self.created_at or datetime.now(timezone.utc),
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
            created_at=self.created_at or datetime.now(timezone.utc),
            updated_at=self.updated_at or datetime.now(timezone.utc)
        ) 

class ModelInfoDTO(BaseModel):
    id: Optional[int] = None
    model_id: str
    name: str
    type: ModelType
    is_local: bool = False
    is_active: bool = False
    compatible: bool = False
    description: Optional[str] = None
    downloads: Optional[int] = None
    likes: Optional[int] = None
    tags: Optional[List[str]] = None
    local_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_info_metadata: Optional[Dict] = None

    @classmethod
    def from_db_model(cls, model: ModelInfo) -> "ModelInfoDTO":
        return cls(
            id=model.id,
            model_id=model.model_id,
            name=model.name,
            type=model.type,
            compatible=True,
            description=model.description,
            downloads=model.downloads,
            likes=model.likes,
            tags=model.tags,
            is_local=model.is_local,
            is_active=model.is_active,
            local_path=model.local_path,
            file_hash=model.file_hash,
            file_size=model.file_size,
            created_at=model.created_at,
            last_used=model.last_used,
            updated_at=model.updated_at,
            model_info_metadata=model.model_info_metadata
        )

    @classmethod
    def from_huggingface(cls, model: HFModelInfo) -> "ModelInfoDTO":
        model_name = (
            model.card_data.model_name 
            if model.card_data and hasattr(model.card_data, 'model_name')
            else model.id
        )
        
        description = (
            model.card_data.to_dict().get('description', '') 
            if model.card_data and hasattr(model.card_data, 'to_dict')
            else ''
        )
        
        metadata = {
            "library_name": model.library_name if hasattr(model, 'library_name') else None,
            "pipeline_tag": model.pipeline_tag if hasattr(model, 'pipeline_tag') else None,
        }
        
        return cls(
            model_id=model.id,
            name=model_name,
            type=ModelType.TEXT,
            compatible=True,
            description=description,
            downloads=model.downloads if hasattr(model, 'downloads') else 0,
            likes=model.likes if hasattr(model, 'likes') else 0,
            tags=model.tags if hasattr(model, 'tags') else [],
            is_local=False,
            is_active=True,
            local_path=None,
            file_hash=None,
            file_size=None,
            created_at=model.created_at if hasattr(model, 'created_at') else datetime.now(timezone.utc),
            last_used=None,
            updated_at=datetime.now(timezone.utc),
            model_info_metadata=metadata
        )
    @validate_db_model
    def to_db_model(self) -> ModelInfo:
        return ModelInfo(
            model_id=self.model_id,
            name=self.name,
            type=self.type,
            compatible=self.compatible,
            description=self.description,
            downloads=self.downloads,
            likes=self.likes,
            tags=self.tags,
            is_local=self.is_local,
            is_active=self.is_active,
            local_path=self.local_path,
            file_hash=self.file_hash,
            file_size=self.file_size,
            created_at=self.created_at or datetime.now(timezone.utc),
            last_used=self.last_used,
            updated_at=self.updated_at or datetime.now(timezone.utc),
            model_info_metadata=self.model_info_metadata
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "model_id": self.model_id,
            "name": self.name,
            "type": self.type.value,
            "compatible": self.compatible,
            "description": self.description,
            "downloads": self.downloads,
            "likes": self.likes,
            "tags": self.tags,
            "is_local": self.is_local,
            "is_active": self.is_active,
            "local_path": self.local_path,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "model_info_metadata": self.model_info_metadata
        }