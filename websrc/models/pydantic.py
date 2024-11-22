# /app.py

import asyncio
import logging
import os
from enum import Enum
from fastapi import Form
from pydantic import BaseModel, Field, field_validator, validator
from typing import Literal, Optional
from src.models.enum import TextModelName, ImageModelName

# Pydantic Models
class ModelConfig(BaseModel):
    model_type: str = Field(..., description="Type of model (text or image)")
    model_name: str = Field(..., description="Name of the model to use")

    model_config = {
        'protected_namespaces': ()
    }

    @field_validator('model_name')
    def validate_model_name(cls, v, info):
        model_type = info.data.get('model_type')
        if model_type == "text":
            model = TextModelName._missing_(v)
            if model is None:
                raise ValueError(f"Invalid text model name: {v}")
            return v
        if model_type == "image":
            model = ImageModelName._missing_(v)
            if model is None:
                raise ValueError(f"Invalid image model name: {v}")
            return v
        return v

class TextGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for generation")
    
    model_config = {
        'protected_namespaces': ()
    }

    @validator('prompt')
    def sanitize_prompt(cls, v):
        # Implement necessary sanitation
        return v.strip()

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Image prompt for generation")
    resolution: str = Field("512x512", description="Image resolution in format WxH")
    
    model_config = {
        'protected_namespaces': ()
    }

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
    model_type: str
    max_length: Optional[int] = 1000
    temperature: Optional[float] = 0.7