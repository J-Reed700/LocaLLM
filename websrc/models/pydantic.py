from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from src.models.enum import TextRepoName, ImageRepoName


class TextGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for generation")
    conversation_id: int = Field(..., description="ID of the conversation")
    type: Optional[str] = Field(default="text", description="Model type (text/image)")
    name: Optional[str] = Field(default=None, description="Model name")
    max_length: Optional[int] = Field(default=1000, description="Maximum length of generated text")
    temperature: Optional[float] = Field(default=0.9, description="Temperature for generation")

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
    resolution: Optional[str] = Field(default="512x512", description="Image resolution in format WxH")
    
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
    type: Optional[str] = "text"
    name: Optional[str] = None
    max_length: Optional[int] = 1000
    temperature: Optional[float] = 0.7

    model_config = ConfigDict(
        protected_namespaces=()
    )


class ModelDownloadRequest(BaseModel):
    model_id: str
    type: str

class ModelDeleteRequest(BaseModel):
    model_id: str
    type: str

class ModelSelectRequest(BaseModel):
    model_id: str
    type: str