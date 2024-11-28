from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from src.models.enum import ModelType, TextModelName, ImageModelName
from src.models.database import MessageRoleEnum

class ModelConfig(BaseModel):

    type: str = Field(..., example="text", alias="model_type")
    name: str = Field(..., example="name", alias="model_name")

    parameters: Dict[str, Any] = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1
    }

    model_config = ConfigDict(
        protected_namespaces=(),
        populate_by_name=True,
        alias_generator=None
    )

    @field_validator('name')
    def validate_model_name(cls, v, values):
        model_type = values.data.get('type')
        if model_type == 'text':
            if not TextModelName.validate(v):
                raise ValueError(f"Invalid text model name: {v}")
        elif model_type == 'image':
            if not ImageModelName.validate(v):
                raise ValueError(f"Invalid image model name: {v}")
        return v

class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1)
    type: str = Field(..., example="text")
    name: str = Field(..., example="model_name")

class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)

class ConversationUpdate(BaseModel):
    """Model for updating conversation details"""
    title: str
    metadata: Optional[Dict] = None

class ConversationUpdate(BaseModel):
    """Model for updating conversation details"""
    title: str

class ChatSettings(BaseModel):
    model_name: str = Field(..., example="gpt2")
    max_length: int = Field(..., ge=1, le=2000, example=1000)

    @field_validator('model_name')
    def validate_model_name(cls, v):
        if not TextModelName.validate(v):
            raise ValueError(f"Invalid text model name: {v}")
        return v

class APISettings(BaseModel):
    rate_limit: int = Field(..., ge=1, le=1000, example=100)