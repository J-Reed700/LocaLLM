from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
import logging
import jinja2
from websrc.models.pydantic import TextModelName
from fastapi.templating import Jinja2Templates
from websrc.config.logging_config import log_async_function

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="websrc/templates")

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Serve Landing Page",
    description="Serves the landing page.",
)
@log_async_function
async def serve_landing(request: Request):
    """Serve the landing page"""
    try:
        return templates.TemplateResponse(
            "landing.html",
            {"request": request}
        )
    except jinja2.exceptions.TemplateNotFound:
        logger.error("Template 'landing.html' not found in templates directory")
        raise HTTPException(
            status_code=500,
            detail="Template not found. Please ensure landing.html exists in the templates directory."
        )

@router.get(
    "/home",
    response_class=HTMLResponse,
    summary="Serve Home Page",
    description="Serves the main chat interface.",
)
@log_async_function
async def serve_home(request: Request):
    """Serve the main chat interface"""
    try:
        text_model_names = [name.value for name in TextModelName]
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "text_model_names": text_model_names}
        )
    except jinja2.exceptions.TemplateNotFound:
        logger.error("Template 'index.html' not found in templates directory")
        raise HTTPException(
            status_code=500,
            detail="Template not found. Please ensure index.html exists in the templates directory."
        )

@router.get(
    "/settings",
    response_class=HTMLResponse,
    summary="Serve Settings Page",
    description="Serves the settings page.",
)
@log_async_function
async def serve_settings(request: Request):
    """Serve the settings page"""
    try:
        text_model_names = [name.value for name in TextModelName]
        return templates.TemplateResponse(
            "settings.html",
            {"request": request, "text_model_names": text_model_names}
        )
    except jinja2.exceptions.TemplateNotFound:
        logger.error("Template 'settings.html' not found in templates directory")
        raise HTTPException(
            status_code=500,
            detail="Template not found. Please ensure settings.html exists in the templates directory."
        )

@router.get(
    "/api",
    response_class=HTMLResponse,
    summary="Serve API Page",
    description="Serves the API documentation page.",
)
@log_async_function
async def serve_api(request: Request):
    """Serve the API documentation page"""
    try:
        return templates.TemplateResponse(
            "api.html",
            {"request": request}
        )
    except jinja2.exceptions.TemplateNotFound:
        logger.error("Template 'api.html' not found in templates directory")
        raise HTTPException(
            status_code=500,
            detail="Template not found. Please ensure api.html exists in the templates directory."
        )