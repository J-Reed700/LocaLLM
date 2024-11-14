# /app.py

import logging
import os
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

import torch
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, BaseSettings, validator
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageGeneration,
    AutoTokenizer,
)
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    OTLPSpanExporter,
)
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from aiocache import cached, Cache
import uvicorn
from typing_extensions import Literal

import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ],
)
logger: logging.Logger = logging.getLogger("locaLLM")

resource = Resource(attributes={
    "service.name": "locaLLM",
    "service.version": "1.1.0",
    "environment": os.getenv("ENVIRONMENT", "production"),
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer("locaLLMTracer")
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
)
trace.get_tracer_provider().add_span_processor(span_processor)

LoggingInstrumentor().instrument(set_logging_format=True)
RequestsInstrumentor().instrument()

app: FastAPI = FastAPI(
    title="locaLLM Server",
    description="A cutting-edge LLM and Image Generation server with seamless scalability and observability",
    version="1.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

FastAPIInstrumentor.instrument_app(app)

class Settings(BaseSettings):
    MODEL_TYPE: Literal["text", "image"] = "text"
    MODEL_NAME: str = "falcon-40b-instruct"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True

settings: Settings = Settings()

class ModelType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

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

class ModelConfig(BaseModel):
    model_type: ModelType = Field(..., description="Type of the model, either 'text' or 'image'")
    model_name: str = Field(..., description="Name of the model to be used")

    @validator('model_name')
    def validate_model_name(cls, v, values):
        model_type = values.get('model_type')
        if model_type == ModelType.TEXT:
            if v not in TextModelName._value2member_map_:
                raise ValueError(f"Invalid text model name: {v}")
        elif model_type == ModelType.IMAGE:
            if v not in ImageModelName._value2member_map_:
                raise ValueError(f"Invalid image model name: {v}")
        return v

class TextGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for text generation")
    max_length: int = Field(1000, description="Maximum length of the generated text")

    @validator('max_length')
    def check_max_length(cls, v):
        if not (10 <= v <= 5000):
            raise ValueError("max_length must be between 10 and 5000")
        return v

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for image generation")
    resolution: str = Field("512x512", description="Resolution of the generated image")

    @validator('resolution')
    def validate_resolution(cls, v):
        if not isinstance(v, str) or 'x' not in v:
            raise ValueError("Resolution must be in the format 'WIDTHxHEIGHT', e.g., '512x512'")
        width, height = v.lower().split('x')
        if not (width.isdigit() and height.isdigit()):
            raise ValueError("Width and Height must be integers")
        return v

class BaseAppError(Exception):
    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)

class ModelConfigurationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)

class InvalidModelTypeError(ModelConfigurationError):
    pass

class InvalidModelNameError(ModelConfigurationError):
    pass

class ModelLoadingError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class TextGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class ImageGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

@app.exception_handler(BaseAppError)
async def base_app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    logger.error(f"{exc.__class__.__name__}: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


def get_model_and_tokenizer_sync(model_type: ModelType, model_name: str) -> Dict[str, Any]:
    logger.info(f"Loading model and tokenizer for {model_type.value} model: {model_name}")
    try:
        if model_type == ModelType.TEXT:
            model_enum = TextModelName(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_enum.value)
            model = AutoModelForCausalLM.from_pretrained(
                model_enum.value,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
            ).eval()
            return {"model": model, "tokenizer": tokenizer}
        elif model_type == ModelType.IMAGE:
            model_enum = ImageModelName(model_name)
            tokenizer = None
            model = AutoModelForImageGeneration.from_pretrained(
                model_enum.value,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
            ).eval()
            return {"model": model, "tokenizer": tokenizer}
        else:
            raise InvalidModelTypeError("Invalid model type")
    except Exception as e:
        logger.exception("Failed to load model")
        raise ModelLoadingError(f"Error loading model: {str(e)}")

async def load_model_async(model_type: ModelType, model_name: str) -> Dict[str, Any]:
    return await asyncio.get_event_loop().run_in_executor(
        None, get_model_and_tokenizer_sync, model_type, model_name
    )

def trace_and_log(span_name: str, log_message_func: Callable[..., str], attributes_func: Optional[Callable[[], Dict[str, Any]]] = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                request: Optional[Request] = kwargs.get('request') or (args[0] if args else None)
                log_message: str = log_message_func(*args, **kwargs)
                attributes: Dict[str, Any] = attributes_func(*args, **kwargs) if attributes_func else {}
                log_and_set_attributes(span, log_message, attributes)
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                request: Optional[Request] = kwargs.get('request') or (args[0] if args else None)
                log_message: str = log_message_func(*args, **kwargs)
                attributes: Dict[str, Any] = attributes_func(*args, **kwargs) if attributes_func else {}
                log_and_set_attributes(span, log_message, attributes)
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

def log_and_set_attributes(span: Any, log_message: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    logger.info(log_message)
    if attributes:
        span.set_attributes(attributes)

def cache_response(ttl: int = settings.CACHE_TTL):
    def decorator(func: Callable):
        return cached(ttl=ttl, cache=Cache.MEMORY)(func)
    return decorator

@app.get(
    "/",
    response_model=Dict[str, str],
    summary="Root Endpoint",
    description="Returns a welcome message.",
    tags=["Root"],
)
@trace_and_log(
    span_name="read_root",
    log_message_func=lambda: "Root endpoint accessed",
    attributes_func=lambda: {"endpoint": "root"}
)
async def read_root() -> Dict[str, str]:
    return {"message": "Welcome to the locaLLM Server, where magic happens"}

@app.post(
    "/generate/text/",
    response_model=Dict[str, str],
    summary="Generate Text",
    description="Generates text based on the provided prompt.",
    tags=["Generation"],
)
@trace_and_log(
    span_name="generate_text",
    log_message_func=lambda request: f"Text generation request received with prompt: {request.prompt}",
    attributes_func=lambda request: {"prompt_length": len(request.prompt)}
)
@cache_response()
async def generate_text(
    request: TextGenerationRequest,
    models: Dict[str, Any] = Depends(
        lambda: asyncio.create_task(load_model_async(ModelType.TEXT, settings.MODEL_NAME))
    ),
) -> Dict[str, str]:
    try:
        if not models or "model" not in models or "tokenizer" not in models:
            raise HTTPException(status_code=400, detail="Invalid text model configuration")
        tokenizer: AutoTokenizer = models["tokenizer"]
        model: AutoModelForCausalLM = models["model"]
        input_ids = tokenizer.encode(request.prompt, return_tensors="pt").to(model.device)
        output_ids = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate(
                input_ids,
                max_length=request.max_length,
                do_sample=True,
                temperature=0.9,
                top_p=0.85,
            ),
        )
        generated_text: str = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return {"generated_text": generated_text}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Text generation failed")
        raise TextGenerationError(f"Error generating text: {str(e)}")

@app.post(
    "/generate/image/",
    response_model=Dict[str, str],
    summary="Generate Image",
    description="Generates an image based on the provided prompt.",
    tags=["Generation"],
)
@trace_and_log(
    span_name="generate_image",
    log_message_func=lambda request: f"Image generation request received with prompt: {request.prompt}",
    attributes_func=lambda request: {"prompt_length": len(request.prompt), "resolution": request.resolution}
)
@cache_response()
async def generate_image(
    request: ImageGenerationRequest,
    models: Dict[str, Any] = Depends(
        lambda: asyncio.create_task(load_model_async(ModelType.IMAGE, settings.MODEL_NAME))
    ),
) -> Dict[str, str]:
    try:
        if not models or "model" not in models:
            raise HTTPException(status_code=400, detail="Invalid image model configuration")
        model: AutoModelForImageGeneration = models["model"]
        generated_image: str = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate(
                prompt=request.prompt,
                resolution=request.resolution
            )
        )
        return {"generated_image": generated_image}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Image generation failed")
        raise ImageGenerationError(f"Error generating image: {str(e)}")

@app.post(
    "/configure/",
    response_model=Dict[str, str],
    summary="Configure Model",
    description="Configures the model type and name for the server.",
    tags=["Configuration"],
)
@trace_and_log(
    span_name="configure_model",
    log_message_func=lambda config: f"Configuring model: {config.model_type.value} - {config.model_name}",
    attributes_func=lambda config: {
        "model_type": config.model_type.value,
        "model_name": config.model_name
    }
)
async def configure_model(config: ModelConfig) -> Dict[str, str]:
    try:
        settings.MODEL_TYPE = config.model_type
        settings.MODEL_NAME = config.model_name
        os.environ["MODEL_TYPE"] = config.model_type.value
        os.environ["MODEL_NAME"] = config.model_name
        logger.info(f"Model configured to use {config.model_type.value} model {config.model_name}")
        return {
            "message": f"Model configured to use {config.model_type.value} model {config.model_name}"
        }
    except ModelConfigurationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.exception("Failed to configure model")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down locaLLM Server...")
    await asyncio.sleep(1)
    logger.info("Shutdown complete.")

@app.get(
    "/health/",
    response_model=Dict[str, str],
    summary="Health Check",
    description="Returns the health status of the server.",
    tags=["Health"],
)
@trace_and_log(
    span_name="health_check",
    log_message_func=lambda: "Health check requested",
    attributes_func=lambda: {"status": "healthy"}
)
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}
