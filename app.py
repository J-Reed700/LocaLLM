# /app.py

# Import statements
from enum import Enum
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional

import torch
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageGeneration,
    AutoTokenizer,
)
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)
LoggingInstrumentor().instrument(set_logging_format=True)
RequestsInstrumentor().instrument()

# FastAPI app initialization
app: FastAPI = FastAPI(
    title="locaLLM Server",
    description="A sleek and powerful LLM and Image Generation server",
    version="1.1",
)
FastAPIInstrumentor.instrument_app(app)

# /app.py/config.py
class Config:
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "text")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "falcon-40b-instruct")

config: Config = Config()

# /app.py/models/model_types.py
# Enum classes for model types and names
class ModelType(str, Enum):
    TEXT = "text"
    IMAGE = "image"

# /app.py/models/text_model_names.py
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

# /app.py/models/image_model_names.py
class ImageModelName(str, Enum):
    STABLE_DIFFUSION_V1 = "stable-diffusion-v1"
    DALLE_MINI = "dalle-mini"
    MIDJOURNEY = "midjourney"
    DALLE_2 = "dalle-2"

# /app.py/models/model_config.py
class ModelConfig(BaseModel):
    model_type: ModelType = Field(..., description="Type of the model, either 'text' or 'image'")
    model_name: str = Field(..., description="Name of the model to be used")

# /app.py/models/requests.py
class TextGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for text generation")
    max_length: int = Field(1000, description="Maximum length of the generated text")

class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for image generation")
    resolution: str = Field("512x512", description="Resolution of the generated image")

# /app.py/exceptions.py
class ModelConfigurationError(Exception):
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(self.message)

class InvalidModelTypeError(ModelConfigurationError):
    pass

class InvalidModelNameError(ModelConfigurationError):
    pass

class ModelLoadingError(Exception):
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(self.message)

class TextGenerationError(Exception):
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(self.message)

class ImageGenerationError(Exception):
    def __init__(self, message: str) -> None:
        self.message: str = message
        super().__init__(self.message)

@app.exception_handler(ModelConfigurationError)
async def model_configuration_error_handler(request: Request, exc: ModelConfigurationError) -> JSONResponse:
    logger.error(f"Model configuration error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )

@app.exception_handler(ModelLoadingError)
async def model_loading_error_handler(request: Request, exc: ModelLoadingError) -> JSONResponse:
    logger.error(f"Model loading error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message},
    )

@app.exception_handler(TextGenerationError)
async def text_generation_error_handler(request: Request, exc: TextGenerationError) -> JSONResponse:
    logger.error(f"Text generation error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message},
    )

@app.exception_handler(ImageGenerationError)
async def image_generation_error_handler(request: Request, exc: ImageGenerationError) -> JSONResponse:
    logger.error(f"Image generation error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message},
    )

# /app.py/utils.py
def get_model_and_tokenizer(config: ModelConfig) -> Dict[str, Any]:
    logger.info(f"Loading model and tokenizer for {config.model_type} model: {config.model_name}")
    try:
        if config.model_type == ModelType.TEXT:
            model_enum: TextModelName = TextModelName(config.model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_enum.value)
            model = AutoModelForCausalLM.from_pretrained(
                model_enum.value,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
            )
            return {"type": "text", "tokenizer": tokenizer, "model": model}
        elif config.model_type == ModelType.IMAGE:
            model_enum: ImageModelName = ImageModelName(config.model_name)
            tokenizer = None  # Image models may not require a tokenizer
            model = AutoModelForImageGeneration.from_pretrained(
                model_enum.value,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
            )
            return {"type": "image", "tokenizer": tokenizer, "model": model}
        else:
            raise InvalidModelTypeError("Invalid model type")
    except Exception as e:
        raise ModelLoadingError(f"Error loading model: {str(e)}")

def log_and_set_attributes(span: Any, log_message: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    logger.info(log_message)
    if attributes:
        span.set_attributes(attributes)

def trace_and_log(span_name: str, log_message_func: Callable[..., str], attributes_func: Optional[Callable[..., Dict[str, Any]]] = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                request: Any = kwargs.get('request') or args[0]  # Assumes request is the first arg or keyword
                log_message: str = log_message_func(*args, **kwargs)
                attributes: Dict[str, Any] = attributes_func(*args, **kwargs) if attributes_func else {}
                log_and_set_attributes(span, log_message, attributes)
                return func(*args, **kwargs)
        return wrapper
    return decorator

# /app.py/routes.py
@app.get("/")
@trace_and_log(
    span_name="read_root",
    log_message_func=lambda: "Root endpoint accessed",
    attributes_func=lambda: {"endpoint": "root"}
)
def read_root() -> Dict[str, str]:
    return {"message": "Welcome to the locaLLM Server, where magic happens"}

@app.post("/generate/text/")
@trace_and_log(
    span_name="generate_text",
    log_message_func=lambda request: f"Text generation request received with prompt: {request.prompt}",
    attributes_func=lambda request: {"prompt": request.prompt}
)
def generate_text(
    request: TextGenerationRequest,
    dependencies: Dict[str, Any] = Depends(
        lambda: get_model_and_tokenizer(
            ModelConfig(model_type=ModelType.TEXT, model_name=config.MODEL_NAME)
        )
    ),
) -> Dict[str, str]:
    try:
        if dependencies is None or dependencies.get("type") != "text":
            raise HTTPException(
                status_code=400, detail="Invalid text model configuration"
            )
        tokenizer, model = dependencies["tokenizer"], dependencies["model"]
        input_ids = tokenizer.encode(request.prompt, return_tensors="pt").to(model.device)
        output_ids = model.generate(
            input_ids,
            max_length=request.max_length,
            do_sample=True,
            temperature=1.0,
            top_p=0.9,
        )
        generated_text: str = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return {"generated_text": generated_text}
    except Exception as e:
        raise TextGenerationError(f"Error generating text: {str(e)}")

@app.post("/generate/image/")
@trace_and_log(
    span_name="generate_image",
    log_message_func=lambda request: f"Image generation request received with prompt: {request.prompt}",
    attributes_func=lambda request: {"prompt": request.prompt}
)
def generate_image(
    request: ImageGenerationRequest,
    dependencies: Dict[str, Any] = Depends(
        lambda: get_model_and_tokenizer(
            ModelConfig(model_type=ModelType.IMAGE, model_name=config.MODEL_NAME)
        )
    ),
) -> Dict[str, str]:
    try:
        if dependencies is None or dependencies.get("type") != "image":
            raise HTTPException(
                status_code=400, detail="Invalid image model configuration"
            )
        model = dependencies["model"]
        # Example generation logic; actual implementation depends on the model's API
        generated_image: str = model.generate(
            prompt=request.prompt, resolution=request.resolution
        )
        return {"generated_image": generated_image}
    except Exception as e:
        raise ImageGenerationError(f"Error generating image: {str(e)}")

@app.post("/configure/")
@trace_and_log(
    span_name="configure_model",
    log_message_func=lambda config: f"Configuring model: {config.model_type} - {config.model_name}",
    attributes_func=lambda config: {
        "model_type": config.model_type.value,
        "model_name": config.model_name
    }
)
def configure_model(config: ModelConfig) -> Dict[str, str]:
    try:
        if config.model_type == ModelType.TEXT:
            if config.model_name not in TextModelName.__members__:
                raise InvalidModelNameError("Invalid text model name")
        elif config.model_type == ModelType.IMAGE:
            if config.model_name not in ImageModelName.__members__:
                raise InvalidModelNameError("Invalid image model name")
        else:
            raise InvalidModelTypeError("Invalid model type")
        
        os.environ["MODEL_TYPE"] = config.model_type.value
        os.environ["MODEL_NAME"] = config.model_name
        return {
            "message": f"Model configured to use {config.model_type.value} model {config.model_name}"
        }
    except ModelConfigurationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
