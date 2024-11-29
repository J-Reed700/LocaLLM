import asyncio
import logging
import os
from enum import Enum
from fastapi import Form
from pydantic import BaseModel, Field, field_validator, validator
from typing import Literal, Optional

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

    @classmethod
    def _convert_value(cls, value: str) -> str:
        """Convert a value to the enum format"""
        if value in cls.__members__:
            return value
        # Try to find a case-insensitive match
        for member in cls:
            if member.value.lower() == value.lower():
                return member.name
            # Also try matching with underscores instead of hyphens
            if member.value.replace('-', '_').lower() == value.replace('-', '_').lower():
                return member.name
        return value

    @classmethod
    def validate(cls, value: str) -> bool:
        """Validate if a value is valid for this enum"""
        converted = cls._convert_value(value)
        return converted in cls.__members__

class ImageModelName(str, Enum):
    STABLE_DIFFUSION_V1 = "stable-diffusion-v1"
    DALLE_MINI = "dalle-mini"
    MIDJOURNEY = "midjourney"
    DALLE_2 = "dalle-2"
    
    @classmethod
    def _convert_value(cls, value: str) -> str:
        """Convert a value to the enum format"""
        if value in cls.__members__:
            return value
        # Try to find a case-insensitive match
        for member in cls:
            if member.value.lower() == value.lower():
                return member.name
            # Also try matching with underscores instead of hyphens
            if member.value.replace('-', '_').lower() == value.replace('-', '_').lower():
                return member.name
        return value

    @classmethod
    def validate(cls, value: str) -> bool:
        """Validate if a value is valid for this enum"""
        converted = cls._convert_value(value)
        return converted in cls.__members__