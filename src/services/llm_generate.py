from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import asyncio

from src.models.pydantic import ModelConfig
from websrc.models.pydantic import TextGenerationRequest, ImageGenerationRequest
from src.models.enum import ModelType, TextModelName, ImageModelName
from websrc.api.exceptions.exceptions import (
    ModelConfigurationError, 
    ModelLoadingError, 
    TextGenerationError, 
    ImageGenerationError
)
from websrc.config.settings import settings
from websrc.config.logging_config import LoggerMixin

@dataclass
class ModelResources:
    """Track model resource usage and settings"""
    max_memory: str = "4GB"
    cpu_threads: int = 4
    device: str = "cpu"
    precision: str = "fp16"
    context_length: int = 2048
    batch_size: int = 1

class BaseModelHandler(ABC, LoggerMixin):
    def __init__(self, model_config: ModelConfig, resources: Optional[ModelResources] = None):
        self.model_config = model_config
        self.resources = resources or ModelResources()
        self._executor = ThreadPoolExecutor(max_workers=self.resources.cpu_threads)
        self._initialize()

    def _initialize(self):
        """Initialize model resources and settings"""
        self.model, self.tokenizer = self.load_model()
        self._setup_model_parameters()
        self.logger.info(f"Initialized {self.__class__.__name__} with {self.resources}")

    @abstractmethod
    def _setup_model_parameters(self):
        """Configure model-specific parameters"""
        pass

    @abstractmethod
    def load_model(self) -> Tuple[Any, Any]:
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Any:
        pass

    def __del__(self):
        self._executor.shutdown(wait=False)

class TextModelHandler(BaseModelHandler):
    def _setup_model_parameters(self):
        self.generation_config = {
            "temperature": self.model_config.parameters.get("temperature", 0.7),
            "top_p": self.model_config.parameters.get("top_p", 0.9),
            "top_k": self.model_config.parameters.get("top_k", 50),
            "repetition_penalty": self.model_config.parameters.get("repetition_penalty", 1.1),
        }

    @lru_cache(maxsize=1)  # Cache the model loading
    def load_model(self) -> Tuple[Any, Any]:
        self.logger.info(f"Loading text model: {self.model_config.model_name}")
        try:
            # Placeholder for actual loading
            return None, None
        except Exception as e:
            self.logger.exception("Failed to load text model")
            raise ModelLoadingError(f"Error loading text model: {str(e)}")

    async def generate_async(self, prompt: str, **kwargs) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self.generate, prompt, **kwargs
        )

    def generate(self, prompt: str, **kwargs) -> str:
        self.logger.info(f"Generating text with prompt: {prompt[:50]}...")
        try:
            # Placeholder: Replace with actual text generation logic
            return f"Generated text based on prompt: {prompt}"
        except Exception as e:
            self.logger.exception("Text generation failed")
            raise TextGenerationError(f"Error generating text: {str(e)}")

class ImageModelHandler(BaseModelHandler):
    def _setup_model_parameters(self):
        self.generation_config = {
            "temperature": self.model_config.parameters.get("temperature", 0.7),
            "top_p": self.model_config.parameters.get("top_p", 0.9),
            "top_k": self.model_config.parameters.get("top_k", 50),
            "repetition_penalty": self.model_config.parameters.get("repetition_penalty", 1.1),
        }

    @lru_cache(maxsize=1)  # Cache the model loading
    def load_model(self) -> Tuple[Any, Any]:
        self.logger.info(f"Loading image model: {self.model_config.model_name}")
        try:
            # Placeholder: Replace with actual model loading logic
            return None, None
        except Exception as e:
            self.logger.exception("Failed to load image model")
            raise ModelLoadingError(f"Error loading image model: {str(e)}")

    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Asynchronous generation using thread pool"""
        return await self._executor.submit(self.generate, prompt, **kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        self.logger.info(f"Generating image with prompt: {prompt[:50]} at resolution {kwargs['resolution']}")
        try:
            # Placeholder: Replace with actual image generation logic
            return f"https://placehold.co/{kwargs['resolution']}/png"
        except Exception as e:
            self.logger.exception("Image generation failed")
            raise ImageGenerationError(f"Error generating image: {str(e)}")

class ModelFactory:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_handler(self, model_config: ModelConfig) -> BaseModelHandler:
        if model_config.model_type == ModelType.TEXT:
            return TextModelHandler(model_config)
        elif model_config.model_type == ModelType.IMAGE:
            return ImageModelHandler(model_config)
        else:
            self.logger.error(f"Unsupported model type: {model_config.model_type}")
            raise ModelConfigurationError(f"Unsupported model type: {model_config.model_type}")

class LLMGenerate(LoggerMixin):
    def __init__(self, model_factory: ModelFactory):
        super().__init__()
        self.model_factory = model_factory
        self.model_config = ModelConfig(
            model_type=settings.MODEL_TYPE,
            model_name=settings.MODEL_NAME
        )
        if not self.validate_model_configuration():
            raise ModelConfigurationError(f"Invalid model configuration: {settings.MODEL_NAME} for type {settings.MODEL_TYPE}")
        
        self.handler = self.model_factory.get_handler(self.model_config) if settings.ENABLE_LLM_SERVICE else None
        self.logger.info(f"LLMGenerate initialized with model: {self.model_config.model_name}")

    def validate_model_configuration(self) -> bool:
        """Validate that the configured model exists and is supported"""
        try:
            if self.model_config.model_type == "text":
                return self.model_config.model_name in TextModelName.__members__
            elif self.model_config.model_type == "image":
                return self.model_config.model_name in ImageModelName.__members__
            return False
        except Exception as e:
            self.logger.error(f"Model configuration validation failed: {e}")
            return False

    def configure_model(self, model_type: str, model_name: str):
        self.logger.info(f"Configuring model: Type={model_type}, Name={model_name}")
        self.model_config = ModelConfig(
            model_type=model_type,
            model_name=model_name
        )
        if not self.validate_model_configuration():
            raise ModelConfigurationError(f"Invalid model configuration: {model_name} for type {model_type}")
        
        self.handler = self.model_factory.get_handler(self.model_config) if settings.ENABLE_LLM_SERVICE else None
        self.logger.info(f"Model configured to: {model_type} - {model_name}")

    def generate_text(self, request: TextGenerationRequest) -> str:
        if not settings.ENABLE_LLM_SERVICE:
            self.logger.warning("LLM Service is disabled.")
            return "LLM Service is currently disabled."

        if self.model_config.model_type != ModelType.TEXT:
            self.logger.error("Configured model type is not 'text'")
            raise ModelConfigurationError("Configured model type is not 'text'")
        
        return self.handler.generate(prompt=request.prompt, max_length=request.max_length)

    def generate_image(self, request: ImageGenerationRequest) -> str:
        if not settings.ENABLE_LLM_SERVICE:
            self.logger.warning("LLM Service is disabled.")
            return "LLM Service is currently disabled."
        
        if self.model_config.model_type != ModelType.IMAGE:
            self.logger.error("Configured model type is not 'image'")
            raise ModelConfigurationError("Configured model type is not 'image'")
        
        return self.handler.generate(prompt=request.prompt, resolution=request.resolution)
