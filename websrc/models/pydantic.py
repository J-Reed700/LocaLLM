from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from src.models.enum import TextModelName, ImageModelName


class TextGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for generation")
    conversation_id: int = Field(..., description="ID of the conversation")
    type: str = Field(..., description="Model type (text/image)")
    name: str = Field(..., description="Model name")
    max_length: int = Field(default=1000, description="Maximum length of generated text")
    temperature: float = Field(default=0.7, description="Temperature for generation")

    model_config = ConfigDict(
        protected_namespaces=()
    )
    
    @field_validator('type')
    def validate_type(cls, v):
        if v not in ['text', 'image']:
            raise ValueError("Type must be either 'text' or 'image'")
        return v

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Image prompt for generation")
    resolution: str = Field("512x512", description="Image resolution in format WxH")
    
    model_config = ConfigDict(
        protected_namespaces=()
    )

    @field_validator('resolution')
    def validate_resolution(cls, v):
        try:
            width, height = map(int, v.split('x'))
            if width <= 0 or height <= 0:
                raise ValueError("Resolution dimensions must be positive")
            return v
        except ValueError:
            raise ValueError("Resolution must be in format WxH (e.g. 512x512)")

class TextGenerationInput(BaseModel):
    prompt: str
    conversation_id: int
    type: str
    name: str
    max_length: int
    temperature: float

    model_config = ConfigDict(
        protected_namespaces=()
    )