from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from src.models.enum import ModelType, TextModelName, ImageModelName
from src.models.database import MessageRoleEnum

class ModelConfig(BaseModel):
    model_type: str
    model_name: str
    parameters: Dict[str, Any] = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1
    }

    @field_validator('model_name')
    def validate_model_name(cls, v, info):
        model_type = info.data.get('model_type')
        if model_type == "text" and v not in TextModelName.__members__:
            raise ValueError(f"Invalid text model name: {v}")
        if model_type == "image" and v not in ImageModelName.__members__:
            raise ValueError(f"Invalid image model name: {v}")
        return v

class ConversationCreate(BaseModel):
    title: str
    model_type: ModelType
    model_name: str

class MessageCreate(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict] = None

class ConversationUpdate(BaseModel):
    """Model for updating conversation details"""
    title: str
    metadata: Optional[Dict] = None

class ConversationUpdate(BaseModel):
    """Model for updating conversation details"""
    title: str