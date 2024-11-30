from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import logging
from websrc.config.settings import settings
from src.models.enum import TextRepoName, ImageRepoName
from fastapi.templating import Jinja2Templates
from websrc.config.logging_manager import LoggingManager
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="websrc/templates")
logging_manager = LoggingManager()

@router.get(
    "/configuration/models",
    response_class=JSONResponse,
    summary="Get Model Names",
    description="Returns available model names based on model type.",
)
@logging_manager.log_and_trace("get_model_names")
async def get_model_names(
    request: Request,
    model_type: str,
) -> JSONResponse:
    try:
        if model_type == "text":
            model_names = [name.value for name in TextRepoName]
        else:
            model_names = [name.value for name in ImageRepoName]
        
        return JSONResponse(model_names)
    except Exception as e:
        logger.exception("Failed to get model names")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/configuration/generate-key",
    response_class=HTMLResponse,
    summary="Generate New API Key",
    description="Generates a new API key.",
)
@logging_manager.log_and_trace("generate_api_key")
async def generate_api_key(request: Request) -> HTMLResponse:
    try:
        # Generate a new API key (implement your key generation logic)
        new_key = secrets.token_urlsafe(32)
        # Save the new key to your database/configuration
        return HTMLResponse(content=new_key)
    except Exception as e:
        logger.exception("Failed to generate API key")
        raise HTTPException(status_code=500, detail=str(e))