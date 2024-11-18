from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from src.api.utility.utilities import get_model_and_tokenizer_sync, trace_and_log, cache_response
from src.models.pydantic import ModelType
from src.config.settings import settings
from src.api.exceptions.exceptions import TextGenerationError, ImageGenerationError
from src.config.logging_config import log_async_function
from typing import Any, Callable, Dict, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# HTMX Text Generation Endpoint
@router.post(
    "/htmx/generate/text/",
    response_class=HTMLResponse,
    summary="HTMX Generate Text",
    description="Generates text based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@trace_and_log(
    span_name="htmx_generate_text",
    log_message_func=lambda form_data: f"HTMX Text generation request received with prompt: {form_data['prompt']}",
    attributes_func=lambda form_data: {"prompt_length": len(form_data['prompt'])}
)
@cache_response()
@log_async_function
async def htmx_generate_text(
    request: Request,
    prompt: str = Form(...),
    max_length: int = Form(1000),
    models: Dict[str, Any] = Depends(
        lambda: get_model_and_tokenizer_sync(ModelType.TEXT, settings.MODEL_NAME)
    ),
) -> HTMLResponse:
    try:
        generated_text = "LLM functionality disabled for testing"
        return HTMLResponse(
            f"""
            <div class="response-content">
                <h3>Generated Text:</h3>
                <p class="generated-text">{generated_text}</p>
            </div>
            """
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HTMX Text generation failed")
        raise TextGenerationError(f"Error generating text: {str(e)}")


# HTMX Image Generation Endpoint
@router.post(
    "/htmx/generate/image/",
    response_class=HTMLResponse,
    summary="HTMX Generate Image",
    description="Generates an image based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@trace_and_log(
    span_name="htmx_generate_image",
    log_message_func=lambda form_data: f"HTMX Image generation request received with prompt: {form_data['prompt']}",
    attributes_func=lambda form_data: {
        "prompt_length": len(form_data['prompt']),
        "resolution": form_data['resolution']
    }
)
@cache_response()
@log_async_function
async def htmx_generate_image(
    request: Request,
    prompt: str = Form(...),
    resolution: str = Form("512x512"),
    models: Dict[str, Any] = Depends(
        lambda: get_model_and_tokenizer_sync(ModelType.IMAGE, settings.MODEL_NAME)
    ),
) -> HTMLResponse:
    try:
        generated_image = "https://placehold.co/512x512/png"
        return HTMLResponse(
            f"""
            <div class="response-content">
                <h3>Generated Image:</h3>
                <img src="{generated_image}" alt="Generated image" class="generated-image">
            </div>
            """
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("HTMX Image generation failed")
        raise ImageGenerationError(f"Error generating image: {str(e)}")