from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import asyncio

from src.models.pydantic import ModelConfig
from websrc.models.pydantic import ImageGenerationRequest
from src.models.enum import ModelType, TextRepoName, ImageRepoName
from exceptions.exceptions import (
    ModelConfigurationError, 
    ModelLoadingError, 
    TextGenerationError, 
    ImageGenerationError
)
from websrc.config.settings import settings
from src.services.conversation_context import ConversationContext
from src.services.settings_service import SettingsService
from src.models.pydantic import TextGeneration
from src.models.database import SettingKey, SettingScope
from src.services.conversation_context import ConversationContext

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
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_model_parameters()
        self._initialize()

    def _initialize(self):
        """Initialize model resources and settings"""
        self.model, self.tokenizer = self.load_model()
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
    async def generate_async(self, prompt: str, prompt_only: str, **kwargs) -> Any:
        pass

    def __del__(self):
        self._executor.shutdown(wait=False)

class TextModelHandler(BaseModelHandler):
    def __init__(self, model_config):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(model_config)

    def _setup_model_parameters(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        # Set device based on available hardware
        self.device = "mps" if torch.backends.mps.is_available() else \
                     "cuda" if torch.cuda.is_available() else "cpu"
        
        # Get model path from discovery service
        self.model_discovery = ModelDiscoveryService()
        self.model_path = self.model_discovery._get_model_path(self.model_config.name)
        
        if not self.model_discovery._is_model_downloaded(self.model_config.name):
            raise ModelLoadingError(
                f"Model {self.model_config.name} is not downloaded. "
                "Please download it first from the models page."
            )
        
        self.generation_config = {
            "temperature": self.model_config.parameters.get("temperature", 0.7),
            "top_p": self.model_config.parameters.get("top_p", 0.9),
            "top_k": self.model_config.parameters.get("top_k", 50),
            "repetition_penalty": self.model_config.parameters.get("repetition_penalty", 1.1),
            "max_new_tokens": 1000,
            "pad_token_id": 0,
            "eos_token_id": 0
        }

    async def load_model(self) -> Tuple[Any, Any]:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        from huggingface_hub import HfApi

        self.logger.info(f"Loading text model: {self.model_config.name} on {self.device}")
        
        try:
            # Validate model exists on Hugging Face
            api = HfApi()
            try:
                api.model_info(self.model_config.name)
            except Exception as e:
                raise ModelLoadingError(
                    f"Model {self.model_config.name} not found on Hugging Face. "
                    "Please check the model name and ensure you have the correct token."
                )
            
            # Load tokenizer and model from Hugging Face
            tokenizer = await AutoTokenizer.from_pretrained(
                self.model_config.name,
                trust_remote_code=True
            )
            
            # Configure model loading based on available resources
            model = await AutoModelForCausalLM.from_pretrained(
                self.model_config.name,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            
            return model, tokenizer
        except Exception as e:
            self.logger.exception("Failed to load text model")
            raise ModelLoadingError(f"Error loading text model: {str(e)}")

    async def generate_async(self, prompt: str, prompt_only: str, max_length: int, temperature: float) -> str:
        return await self._executor.submit(self.generate, prompt, prompt_only, max_length, temperature)

    def generate(self, prompt: str, prompt_only: str, max_length: int, temperature: float) -> str:
        self.logger.info(f"Generating text with prompt: {prompt[:50]}...")
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                **self.generation_config
            )
            
            # Decode and clean response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (after the prompt)
            response = response[len(prompt):].strip()
            
            return response
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

    async def generate_async(self, prompt: str, prompt_only: str, **kwargs) -> str:
        """Asynchronous generation using thread pool"""
        return await self._executor.submit(self.generate, prompt, prompt_only, **kwargs)

    def generate(self, prompt: str, prompt_only: str, **kwargs) -> str:
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
    def __init__(self, model_factory: ModelFactory, conversation_context: ConversationContext, settings_service: SettingsService):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_factory = model_factory
        self.model_config = ModelConfig(
            type=settings.GENMODEL_TYPE,
            name=settings.GENMODEL_NAME
        )
        self.conversation_context = conversation_context
        self.settings_service = settings_service

        if not self.validate_model_configuration():
            raise ModelConfigurationError(f"Invalid model configuration: {settings.GENMODEL_NAME} for type {settings.GENMODEL_TYPE}")
        
        self.handler = self.model_factory.get_handler(self.model_config)
        self.logger.info(f"LLMGenerate initialized with model: {self.model_config.name}")

    def validate_model_configuration(self) -> bool:
        """Validate that the configured model exists and is supported"""
        try:
            if self.model_config.type == "text":
                return TextRepoName.validate(self.model_config.name)
            elif self.model_config.type == "image":
                return ImageRepoName.validate(self.model_config.name )
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
        
        self.handler = self.model_factory.get_handler(self.model_config)
        self.logger.info(f"Model configured to: {model_type} - {model_name}")

    async def generate_text(self, request: TextGeneration) -> Dict[str, Any]:
        if self.model_config.type != ModelType.TEXT:
            self.logger.error("Configured model type is not 'text'")
            raise ModelConfigurationError("Configured model type is not 'text'")

        # Process the request and get/create conversation
        conversation, user_message = await self.conversation_context.process_request(request)
        
        # Get conversation history BEFORE adding the new message
        history = await self.conversation_context.get_conversation_history(conversation.id, user_message.id)
        
        # Get system prompt (conversation-specific or cached default)
        system_prompt = conversation.system_prompt
        if not system_prompt:
            system_prompt = await self.settings_service.get_default_system_prompt()
        
        # Format context for LLM with system prompt
        context = self.conversation_context.format_context(history, system_prompt)
        
        # Generate response with context and current prompt
        response = await self.handler.generate_async(
            prompt=f"{context}\nUser: {request.prompt}\nAssistant:",
            prompt_only=request.prompt,
            max_length=request.parameters.max_length,
            temperature=request.parameters.temperature
        )

        # Save assistant response
        assistant_message = await self.conversation_context.add_message(
            conversation.id,
            content=response,
            role="assistant"
        )
        
        return {
            "text": response,
            "conversation_id": conversation.id,
            "messages": [user_message.model_dump(), assistant_message.model_dump()]
        }

    async def generate_image(self, request: ImageGenerationRequest) -> str:
        if self.model_config.type != ModelType.IMAGE:
            self.logger.error("Configured model type is not 'image'")
            raise ModelConfigurationError("Configured model type is not 'image'")
        
        return await self.handler.generate_async(
            prompt=request.prompt,
            resolution=request.resolution
        )