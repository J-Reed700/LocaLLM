from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from src.models.enum import ModelType, TextModelName, ImageModelName

class ModelConfig(BaseModel):
    model_type: ModelType
    model_name: str

    @field_validator('model_name')
    def validate_model_name(cls, v, values):
        model_type = values.get('model_type')
        if model_type == ModelType.TEXT and v not in [m.value for m in TextModelName]:
            raise ValueError(f"Invalid text model name: {v}")
        if model_type == ModelType.IMAGE and v not in [m.value for m in ImageModelName]:
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