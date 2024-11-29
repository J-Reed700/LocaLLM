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

@dataclass
class ModelResources:
    """Track model resource usage and settings"""
    max_memory: str = settings.MODEL_RESOURCES_MAX_MEMORY
    cpu_threads: int = settings.MODEL_RESOURCES_CPU_THREADS
    device: str = settings.MODEL_RESOURCES_DEVICE
    precision: str = settings.MODEL_RESOURCES_PRECISION
    context_length: int = settings.MODEL_RESOURCES_CONTEXT_LENGTH
    batch_size: int = settings.MODEL_RESOURCES_BATCH_SIZE

class BaseModelHandler(ABC):
    def __init__(self, model_config: ModelConfig, resources: Optional[ModelResources] = None):
        self.model_config = model_config
        self.resources = resources or ModelResources()
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
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

    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> Any:
        pass

    def __del__(self):
        self._executor.shutdown(wait=False)

class TextModelHandler(BaseModelHandler):
    def __init__(self, model_config):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(model_config)
        self._executor = ThreadPoolExecutor(max_workers=4)  # Example executor setup

    def _setup_model_parameters(self):
        self.generation_config = {
            "temperature": self.model_config.parameters.get("temperature", 0.7),
            "top_p": self.model_config.parameters.get("top_p", 0.9),
            "top_k": self.model_config.parameters.get("top_k", 50),
            "repetition_penalty": self.model_config.parameters.get("repetition_penalty", 1.1),
        }

    @lru_cache(maxsize=1)  # Cache the model loading
    def load_model(self) -> Tuple[Any, Any]:
        self.logger.info(f"Loading text model: {self.model_config.name}")
        try:
            # Placeholder for actual loading
            return None, None
        except Exception as e:
            self.logger.exception("Failed to load text model")
            raise ModelLoadingError(f"Error loading text model: {str(e)}")

    async def generate_async(self, prompt: str, max_length: int, temperature: float = 0.7) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self.generate, prompt, max_length, temperature
        )

    def generate(self, prompt: str, max_length: int, temperature: float) -> str:
        self.logger.info(f"Generating text with prompt: {prompt[:50]}... Max Length: {max_length}, Temperature: {temperature}")
        try:
            # Replace the following line with actual text generation logic using the model
            return f"Generated text based on prompt: {prompt} with max_length={max_length} and temperature={temperature}"
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
        self.logger.info(f"Loading image model: {self.model_config.name}")
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
        if model_config.type == ModelType.TEXT:
            return TextModelHandler(model_config)
        elif model_config.type == ModelType.IMAGE:
            return ImageModelHandler(model_config)
        else:
            self.logger.error(f"Unsupported model type: {model_config.type}")
            raise ModelConfigurationError(f"Unsupported model type: {model_config.type}")

class LLMGenerate():
    def __init__(self, model_factory: ModelFactory):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_factory = model_factory
        self.model_config = ModelConfig(
            type=settings.GENMODEL_TYPE,
            name=settings.GENMODEL_NAME
        )
        if not self.validate_model_configuration():
            raise ModelConfigurationError(f"Invalid model configuration: {settings.GENMODEL_NAME} for type {settings.GENMODEL_TYPE}")
        
        self.handler = self.model_factory.get_handler(self.model_config) if settings.ENABLE_LLM_SERVICE else None
        self.logger.info(f"LLMGenerate initialized with model: {self.model_config.name}")

    def validate_model_configuration(self) -> bool:
        """Validate that the configured model exists and is supported"""
        try:
            if self.model_config.type == "text":
                return TextModelName.validate(self.model_config.name)
            elif self.model_config.type == "image":
                return ImageModelName.validate(self.model_config.name )
            return False
        except Exception as e:
            self.logger.error(f"Model configuration validation failed: {e}")
            return False

    def configure_model(self, model_type: str, model_name: str):
        self.logger.info(f"Configuring model: Type={model_type}, Name={model_name}")
        self.model_config = ModelConfig(
            type=model_type,
            name=model_name
        )
        if not self.validate_model_configuration():
            raise ModelConfigurationError(f"Invalid model configuration: {model_name} for type {model_type}")
        
        self.handler = self.model_factory.get_handler(self.model_config) if settings.ENABLE_LLM_SERVICE else None
        self.logger.info(f"Model configured to: {model_type} - {model_name}")

    async def generate_text(self, request: TextGenerationRequest) -> str:
        if not settings.ENABLE_LLM_SERVICE:
            self.logger.warning("LLM Service is disabled.")
            return "LLM Service is currently disabled."

        if self.model_config.type != ModelType.TEXT:
            self.logger.error("Configured model type is not 'text'")
            raise ModelConfigurationError("Configured model type is not 'text'")
        
        return await self.handler.generate_async(
            prompt=request.prompt,
            max_length=request.max_length,
            temperature=request.temperature
        )

    async def generate_image(self, request: ImageGenerationRequest) -> str:
        if not settings.ENABLE_LLM_SERVICE:
            self.logger.warning("LLM Service is disabled.")
            return "LLM Service is currently disabled."
        
        if self.model_config.type != ModelType.IMAGE:
            self.logger.error("Configured model type is not 'image'")
            raise ModelConfigurationError("Configured model type is not 'image'")
        
        return await self.handler.generate_async(
            prompt=request.prompt,
            resolution=request.resolution
        )