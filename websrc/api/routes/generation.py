from fastapi import APIRouter, Request, Form, Depends, HTTPException, BackgroundTasks, Body
from fastapi.responses import HTMLResponse, JSONResponse
from websrc.models.pydantic import TextGenerationRequest, ImageGenerationRequest
from websrc.api.exceptions.exceptions import TextGenerationError, ImageGenerationError
from websrc.config.logging_config import log_endpoint, track_span_exceptions
from src.services.container import container, get_llm_generate_service_dependency
from src.services.llm_generate import LLMGenerate
from typing import Optional, Dict, Any
from websrc.api.exceptions.exceptions import BaseAppError, ModelLoadingError, TextGenerationValidationError
import logging
import asyncio
from websrc.models.pydantic import  TextGenerationInput
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

class GenerationResponse:
    """Standardized response formatter"""
    @staticmethod
    def success(content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "success",
            "content": content,
            "metadata": metadata or {}
        }

    @staticmethod
    def error(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "error",
            "message": message,
            "details": details or {}
        }

async def log_generation_request(generation_type: str, prompt: str) -> None:
    """
    Log generation requests for analytics and monitoring
    
    Args:
        generation_type: Type of generation (text/image)
        prompt: The user's input prompt
    """
    try:
        logger.info(
            "Generation request",
            extra={
                "generation_type": generation_type,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
            }
        )
    except Exception as e:
        logger.error(f"Failed to log generation request: {str(e)}")

@router.post(
    "/htmx/generate/text/",
    response_class=HTMLResponse,
    summary="HTMX Generate Text",
    description="Generates text based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@log_endpoint
@track_span_exceptions()
async def htmx_generate_text(
    request: Request,
    llm_service: Optional[LLMGenerate] = Depends(get_llm_generate_service_dependency)
) -> HTMLResponse:
    try:
        if not llm_service:
            return HTMLResponse("<div class='response-content'><p>LLM Service is disabled.</p></div>")
            
        body = await request.json()
        generation_request = TextGenerationRequest(**body)
            
        generated_text = await llm_service.handler.generate_async(
            prompt=generation_request.prompt,
            max_length=generation_request.max_length,
            temperature=generation_request.temperature
        )
        
        if not generated_text:
            raise TextGenerationError("No text was generated")
            
        return HTMLResponse(
            content=generated_text,
            headers={"HX-Trigger": "messageGenerated"}
        )
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/htmx/generate/image/",
    response_class=HTMLResponse,
    summary="HTMX Generate Image",
    description="Generates an image based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@log_endpoint
@track_span_exceptions()
async def htmx_generate_image(
    request: Request,
    llm_service: Optional[LLMGenerate] = Depends(get_llm_generate_service_dependency)
) -> HTMLResponse:
    try:
        if not llm_service:
            return HTMLResponse("<div class='response-content'><p>LLM Service is disabled.</p></div>")

        body = await request.json()
        image_request = ImageGenerationRequest(**body)
        generated_image = llm_service.generate_image(image_request)
        
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
        raise HTTPException(status_code=500, detail=str(e))