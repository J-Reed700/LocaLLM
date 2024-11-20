from fastapi import APIRouter, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from websrc.models.pydantic import TextGenerationRequest, ImageGenerationRequest
from websrc.api.exceptions.exceptions import TextGenerationError, ImageGenerationError
from websrc.config.logging_config import log_async_function
from src.services.container import container
from src.services.llm_generate import LLMGenerate
from typing import Optional, Dict, Any
import logging
import asyncio

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
@log_async_function
async def htmx_generate_text(
    request: Request,
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    max_length: int = Form(1000),
    temperature: float = Form(0.7),
    llm_service: Optional[LLMGenerate] = Depends(container.llm_service)
) -> HTMLResponse:
    try:
        if not llm_service:
            return HTMLResponse(
                GenerationResponse.error("LLM Service is disabled.")
            )

        # Add request to background tasks for logging/analytics
        background_tasks.add_task(log_generation_request, "text", prompt)
        
        text_request = TextGenerationRequest(
            prompt=prompt,
            max_length=max_length,
            parameters={"temperature": temperature}
        )
        
        generated_text = await llm_service.handler.generate_async(
            prompt=text_request.prompt,
            max_length=text_request.max_length
        )
        
        return HTMLResponse(
            GenerationResponse.success(
                generated_text,
                metadata={"prompt_length": len(prompt)}
            )
        )
    except Exception as e:
        logger.exception("HTMX Text generation failed")
        return HTMLResponse(
            GenerationResponse.error(str(e)),
            status_code=500
        )

@router.post(
    "/htmx/generate/image/",
    response_class=HTMLResponse,
    summary="HTMX Generate Image",
    description="Generates an image based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@log_async_function
async def htmx_generate_image(
    request: Request,
    prompt: str = Form(...),
    resolution: str = Form("512x512"),
    llm_service: Optional[LLMGenerate] = Depends(container.llm_service)
) -> HTMLResponse:
    try:
        if not llm_service:
            return HTMLResponse("<div class='response-content'><p>LLM Service is disabled.</p></div>")

        image_request = ImageGenerationRequest(prompt=prompt, resolution=resolution)
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
        raise ImageGenerationError(f"Error generating image: {str(e)}")