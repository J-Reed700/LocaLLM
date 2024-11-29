from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
import logging
from websrc.config.settings import settings
from src.models.enum import TextModelName, ImageModelName
from websrc.api.exceptions.exceptions import (
    InvalidModelTypeError,
    InvalidModelNameError
)
from fastapi.templating import Jinja2Templates
import os
from websrc.config.logging_manager import LoggingManager
from src.models.pydantic import ModelConfig, ChatSettings, APISettings
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="websrc/templates")
logging_manager = LoggingManager()

@router.post(
    "/configure/",
    response_class=HTMLResponse,
    summary="Configure Model",
    description="Configures the model type and name.",
)
@logging_manager.log_and_trace("configure_model")
async def configure_model(
    request: Request,
    config: ModelConfig,
) -> HTMLResponse:
    if config.type not in ["text", "image"]:
        raise InvalidModelTypeError(config.type)
        
    valid_names = TextModelName if config.type == "text" else ImageModelName
    if not any(name.value == config.name for name in valid_names):
        raise InvalidModelNameError(config.name)
        
    settings.GENMODEL_TYPE = config.type
    settings.GENMODEL_NAME = config.name
    return HTMLResponse(content="Model configured successfully")

@router.post(
    "/get_model_names/",
    response_class=HTMLResponse,
    summary="Get Model Names",
    description="Returns available model names based on model type.",
)
@logging_manager.log_and_trace("get_model_names")
async def get_model_names(
    request: Request,
    model_type: str = Form(...),
) -> HTMLResponse:
    try:
        if model_type == "text":
            model_names = [name.value for name in TextModelName]
        else:
            model_names = [name.value for name in ImageModelName]
        
        return templates.TemplateResponse(
            "model_names.html",
            {"request": request, "model_names": model_names}
        )
    except Exception as e:
        logger.exception("Failed to get model names")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/settings/chat",
    response_class=HTMLResponse,
    summary="Configure Chat Settings",
    description="Configures the chat settings including model and max length.",
)
@logging_manager.log_and_trace("configure_chat_settings")
async def configure_chat_settings(
    request: Request,
    settings: ChatSettings,
) -> HTMLResponse:
    try:
        # Here you would save these settings to your configuration/database
        return HTMLResponse(content="Chat settings saved successfully")
    except Exception as e:
        logger.exception("Failed to save chat settings")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/settings/api",
    response_class=HTMLResponse,
    summary="Configure API Settings",
    description="Configures the API settings including rate limits.",
)
@logging_manager.log_and_trace("configure_api_settings" )
async def configure_api_settings(
    request: Request,
    settings: APISettings,
) -> HTMLResponse:
    try:
        # Here you would save these settings to your configuration/database
        return HTMLResponse(content="API settings saved successfully")
    except Exception as e:
        logger.exception("Failed to save API settings")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/settings/api/generate-key",
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