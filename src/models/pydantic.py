from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo
from typing import Optional, Dict, Any
from src.models.enum import ModelType, TextRepoName, ImageRepoName
from src.models.database import SettingValueType, SettingScope, SettingKey
from src.models.dto import ConversationDTO  
from websrc.models.pydantic import TextGenerationRequest
from dataclasses import dataclass
from src.models.database import ModelInfo
from datetime import datetime

class ModelConfig(BaseModel):
    type: ModelType = Field(..., example="text", alias="model_type")
    name: str = Field(..., example="name", alias="model_name")
    parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1
    })

    model_config = ConfigDict(
        protected_namespaces=(),
        populate_by_name=True,
        alias_generator=None
    )

    @field_validator('name')
    def validate_model_name(cls, v: str, info: ValidationInfo) -> str:
        model_type = info.data.get('type', ModelType.TEXT)
        if model_type == ModelType.TEXT:
            if not TextRepoName.validate(v):
                raise ValueError(f"Invalid text model name: {v}")
        elif model_type == ModelType.IMAGE:
            if not ImageRepoName.validate(v):
                raise ValueError(f"Invalid image model name: {v}")
        return v

class APISettings(BaseModel):
    rate_limit: int = Field(..., ge=1, le=1000, example=100)

class SettingCreate(BaseModel):
    key: SettingKey 
    value: Any
    value_type: SettingValueType = Field(default=SettingValueType.STRING)
    scope: SettingScope = Field(default=SettingScope.GLOBAL)
    scope_id: Optional[int] = None

    model_config = ConfigDict(
        protected_namespaces=()
    )

    @field_validator('key')
    def validate_key(cls, v):
        if not v.strip():
            raise ValueError("Setting key cannot be empty")
        return v.strip()

class SettingUpdate(BaseModel):
    value: str
    value_type: Optional[SettingValueType] = Field(default=SettingValueType.STRING)

    model_config = ConfigDict(
        protected_namespaces=()
    )

class SettingResponse(BaseModel):
    key: SettingKey
    value: Any
    value_type: SettingValueType
    scope: SettingScope
    scope_id: Optional[int] = None

    model_config = ConfigDict(
        protected_namespaces=()
    )

class ModelParameters(BaseModel):
    type: ModelType = Field(default=ModelType.TEXT)
    name: str = Field(..., description="Model name is required")
    max_length: int = Field(default=1000)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9, description="Top P for generation")
    top_k: int = Field(default=50, description="Top K for generation")
    repetition_penalty: float = Field(default=1.1, description="Repetition penalty for generation")

    model_config = ConfigDict(
        protected_namespaces=()
    )

class TextGeneration(BaseModel):
    prompt: str = Field(..., description="Text prompt for generation")
    conversation_id: Optional[int] = Field(default=None, description="ID of the conversation")
    parameters: ModelParameters = Field(default_factory=ModelParameters)

    model_config = ConfigDict(
        protected_namespaces=()
    )

    @classmethod
    def map_from_request(cls, request: TextGenerationRequest) -> "TextGeneration":
        return cls(
            prompt=request.prompt,
            conversation_id=request.conversation_id,
            parameters=ModelParameters(
                type=ModelType(request.type) or ModelType.TEXT,
                name=request.name,
                max_length=request.max_length or 1000,
                temperature=request.temperature or 0.7
            )
        )

class ConversationUpdate(BaseModel):
    """Model for updating conversation details"""
    title: str
    system_prompt: Optional[str] = None
    metadata: Optional[Dict] = None

    model_config = ConfigDict(
        protected_namespaces=()
    )

class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1)
    parameters: ModelParameters = Field(default_factory=ModelParameters)
    system_prompt: Optional[str] = None

    @classmethod
    def create(cls, title: str, 
                     type: ModelType, 
                     name: str, 
                     system_prompt: Optional[str] = None,
                     max_length: int = 1000, 
                     temperature: float = 0.9, 
                     top_p: float = 0.9, 
                     top_k: int = 50, 
                     repetition_penalty: float = 1.1) -> "ConversationCreate":
        return cls(
            title=title,
            system_prompt=system_prompt,
            parameters=ModelParameters(
                type=type, 
                name=name, 
                max_length=max_length, 
                temperature=temperature, 
                top_p=top_p, 
                top_k=top_k, 
                repetition_penalty=repetition_penalty
            )
        )

class MessageCreate(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)

@dataclass
class BlobLfsInfo:
    size: int
    sha256: str
    pointer_size: int

@dataclass
class RepoSibling:
    rfilename: str
    size: Optional[int] = None
    blob_id: Optional[str] = None
    lfs: Optional[BlobLfsInfo] = None
    
@dataclass
class ModelInfoView:
    # Required fields (no defaults)
    id: int
    model_id: str
    name: str
    type: ModelType
    created_at: datetime
    updated_at: datetime
    
    # Optional fields (with defaults)
    description: Optional[str] = None
    downloads: Optional[int] = None
    likes: Optional[int] = None 
    tags: Optional[list[str]] = None
    is_local: bool = False
    is_active: bool = False
    local_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    last_used: Optional[datetime] = None
    model_info_metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_orm(cls, db_model: ModelInfo) -> "ModelInfoView":
        return cls(
            id=db_model.id,
            model_id=db_model.model_id,
            name=db_model.name,
            type=db_model.type,
            description=db_model.description,
            downloads=db_model.downloads,
            likes=db_model.likes,
            tags=db_model.tags,
            is_local=db_model.is_local,
            is_active=db_model.is_active,
            local_path=db_model.local_path,
            file_hash=db_model.file_hash,
            file_size=db_model.file_size,
            created_at=db_model.created_at,
            last_used=db_model.last_used,
            updated_at=db_model.updated_at,
            model_info_metadata=db_model.model_info_metadata
        )
    
    def __repr__(self):
        return f"<ModelInfoView(id={self.id}, name='{self.name}', type='{self.type}')>"


class ModelMetadata:
    id: str
    size_bytes: int
    created_at: datetime