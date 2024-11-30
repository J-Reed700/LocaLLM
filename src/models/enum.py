import asyncio
import logging
import os
from enum import Enum
from fastapi import Form
from pydantic import BaseModel, Field, field_validator, validator
from typing import Literal, Optional
import yaml
from pathlib import Path

# Enum Definitions
class DynamicModelEnum:
    @classmethod
    def load_config(cls):
        config_path = Path(__file__).parent / "config" / "models.yaml"
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

class ModelType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

    @classmethod
    def list(cls):
        return [member.value for member in cls]

class TextRepoName(str, Enum):
    def __new__(cls):
        config = DynamicModelEnum.load_config()
        members = {}
        orgs = {}
        
        for org, models in config.get("text_models", {}).items():
            if org not in orgs:
                orgs[org] = []
            for key, value in models.items():
                enum_key = f"{key}".upper().replace("-", "_")
                orgs[org].append(value)
                members[enum_key] = value
                
        return str.__new__(cls)

    @property
    def display_name(self) -> str:
        """Returns a human-readable name for the model"""
        name = self.value.split('/')[-1]
        name = name.replace('-', ' ').title()
        return name

    @property
    def organization(self) -> str:
        """Returns the organization that created the model"""
        return next((org for org, models in self.orgs.items() if self.value in models), None)

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
        return True

class ImageRepoName(str, Enum):
    def __new__(cls):
        config = DynamicModelEnum.load_config()
        config = DynamicModelEnum.load_config()
        members = {}
        orgs = {}
        
        for org, models in config.get("image_models", {}).items():
            if org not in orgs:
                orgs[org] = []
            for key, value in models.items():
                enum_key = f"{key}".upper().replace("-", "_")
                orgs[org].append(value)
                members[enum_key] = value
                
        return str.__new__(cls)

    @property
    def display_name(self) -> str:
        """Returns a human-readable name for the model"""
        name = self.value.split('/')[-1]
        name = name.replace('-', ' ').title()
        return name

    @property
    def organization(self) -> str:
        """Returns the organization that created the model"""
        return next((org for org, models in self.orgs.items() if self.value in models), None)

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
        return True
