from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from websrc.models.pydantic import TextGenerationRequest, ImageGenerationRequest
from src.models.pydantic import TextGeneration
from exceptions.exceptions import TextGenerationError
from src.dependencies.container import LLMDependency
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
    # Map request to domain model
    text_generation = TextGeneration.map_from_request(request)
    result = await llm_service.generate_text(text_generation)
        
    if not result:
        raise TextGenerationError("No text was generated")
    
    # Append response context
    response_text = (
        f"{result['text']}\n\n"
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

@router.post(
    "/api/generate/text/",
    response_class=JSONResponse,
    summary="API Generate Text",
    description="Generates text based on the provided prompt via API.",
    tags=["API Generation"],       
)
@logging_manager.log_and_trace("api_generate_text")
async def api_generate_text(
    request: TextGenerationRequest,
    llm_service: LLMDependency
):
    # Map request to domain model
    text_generation = TextGeneration.map_from_request(request)
    result = await llm_service.generate_text(text_generation)
        
    if not result:
        raise TextGenerationError("No text was generated")
    
    return JSONResponse({
        "text": result["text"],
        "model": text_generation.name or "default"
    })

@router.post(
    "/api/generate/image/",
    response_class=JSONResponse,
    summary="API Generate Image",
    description="Generates an image based on the provided prompt via API.",
    tags=["API Generation"],
)
@logging_manager.log_and_trace("api_generate_image")
async def api_generate_image(
    request: ImageGenerationRequest,
    llm_service: LLMDependency
) -> JSONResponse:
    generated_image = llm_service.generate_image(request)
        
    return JSONResponse({
        "image_url": generated_image,
        "model": "AI model"  # You might want to make this more specific
    })