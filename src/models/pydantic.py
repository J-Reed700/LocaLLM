from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from src.models.enum import ModelType, TextModelName, ImageModelName

class ModelConfig(BaseModel):
    model_type: ModelType
    model_name: str

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