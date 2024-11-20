# /app.py

import asyncio
import logging
import os
from enum import Enum
from fastapi import Form
from pydantic import BaseModel, Field, field_validator, validator
from typing import Literal

# Enum Definitions
class ModelType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

    @classmethod
    def list(cls):
        return [member.value for member in cls]

class TextModelName(str, Enum):
    FALCON_40B_INSTRUCT = "falcon-40b-instruct"
    GPT_NEO_2_7B = "gpt-neo-2.7b"
    GPT_J_6B = "gpt-j-6b"
    GPT_NEO_1_3B = "gpt-neo-1.3b"
    GPT_NEO_125M = "gpt-neo-125m"
    GPT_3_DAVINCI = "gpt-3-davinci"
    GPT_3_CURIE = "gpt-3-curie"
    GPT_3_BABBAGE = "gpt-3-babbage"
    GPT_3_ADA = "gpt-3-ada"
    BLOOM_176B = "bloom-176b"
    BLOOM_7B1 = "bloom-7b1"
    BLOOM_3B = "bloom-3b"
    BLOOM_1B7 = "bloom-1b7"
    BLOOM_560M = "bloom-560m"
    BLOOM_350M = "bloom-350m"
    BLOOM_125M = "bloom-125m"
    LLAMA_13B = "llama-13b"
    LLAMA_7B = "llama-7b"
    LLAMA_2_13B = "llama-2-13b"
    LLAMA_2_7B = "llama-2-7b"

class ImageModelName(str, Enum):
    STABLE_DIFFUSION_V1 = "stable-diffusion-v1"
    DALLE_MINI = "dalle-mini"
    MIDJOURNEY = "midjourney"
    DALLE_2 = "dalle-2"

# Pydantic Models
class ModelConfig(BaseModel):
    model_type: str = Field(..., description="Type of model (text or image)")
    model_name: str = Field(..., description="Name of the model to use")

    model_config = {
        'protected_namespaces': ()
    }

    @field_validator('model_name')
    def validate_model_name(cls, v, values):
        model_type = values.get('model_type')
        if model_type == "text" and v not in TextModelName.__members__:
            raise ValueError(f"Invalid text model name: {v}")
        if model_type == "image" and v not in ImageModelName.__members__:
            raise ValueError(f"Invalid image model name: {v}")
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