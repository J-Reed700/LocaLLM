from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from websrc.models.pydantic import TextGenerationRequest, ImageGenerationRequest
from websrc.api.exceptions.exceptions import TextGenerationError, ImageGenerationError
from src.services.container import LLMDependency
from typing import Optional, Dict, Any
import logging
import asyncio
from websrc.config.logging_manager import LoggingManager

router = APIRouter()
logging_manager = LoggingManager()  


@router.post(
    "/generate/text/",
    response_class=HTMLResponse,
    summary="HTMX Generate Text",
    description="Generates text based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],       
)
@logging_manager.log_and_trace("htmx_generate_text")
async def htmx_generate_text(
    request: TextGenerationRequest,
    llm_service: LLMDependency
):
    generated_text = await llm_service.generate_text(request)
        
    if not generated_text:
        raise TextGenerationError("No text was generated")
    
    # Append response context
    response_text = (
        f"{generated_text}\n\n"
        f"[Response generated using model: {request.model_name if hasattr(request, 'model_name') else 'default'}]"
    )
            
    return HTMLResponse(
        content=response_text,
        headers={"HX-Trigger": "messageGenerated"}
    )

@router.post(
    "/generate/image/",
    response_class=HTMLResponse,
    summary="HTMX Generate Image",
    description="Generates an image based on the provided prompt via HTMX.",
    tags=["HTMX Generation"],
)
@logging_manager.log_and_trace("htmx_generate_image")
async def htmx_generate_image(
    request: Request,
    llm_service: LLMDependency
) -> HTMLResponse:
    body = await request.json()
    image_request = ImageGenerationRequest(**body)
    generated_image = llm_service.generate_image(image_request)
        
    return HTMLResponse(
        f"""
        <div class="response-content">
                <h3>Generated Image:</h3>
                <img src="{generated_image}" alt="Generated image" class="generated-image">
                <p class="text-sm text-gray-500 mt-2">
                    [Image generated using AI model]
                </p>
            </div>
            """
    )