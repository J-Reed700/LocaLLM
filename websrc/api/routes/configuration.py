from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
import logging
from websrc.config.settings import settings
from src.models.enum import TextModelName, ImageModelName
from websrc.api.exceptions.exceptions import ModelConfigurationError
from fastapi.templating import Jinja2Templates
import os
from websrc.config.logging_config import log_async_function

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="websrc/templates")


@router.post(
    "/configure/",
    response_class=HTMLResponse,
    summary="Configure Model",
    description="Configures the model type and name.",
)
async def configure_model(
    request: Request,
    model_type: str = Form(...),
    model_name: str = Form(...),
) -> HTMLResponse:
    try:
        # Basic validation
        if model_type not in ["text", "image"]:
            raise ValueError(f"Invalid model type: {model_type}")
            
        valid_names = TextModelName if model_type == "text" else ImageModelName
        if not any(name.value == model_name for name in valid_names):
            raise ValueError(f"Invalid model name: {model_name}")
            
        settings.MODEL_TYPE = model_type
        settings.MODEL_NAME = model_name
        
        return HTMLResponse(f"<div>Model configured: {model_type} - {model_name}</div>")
    except Exception as e:
        logger.exception("Model configuration failed")
        raise ModelConfigurationError(f"Error configuring model: {str(e)}")

@router.post(
    "/get_model_names/",
    response_class=HTMLResponse,
    summary="Get Model Names",
    description="Returns available model names based on model type.",
)
@log_async_function
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