from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
import logging
import jinja2
from websrc.models.pydantic import TextRepoName
from fastapi.templating import Jinja2Templates
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from websrc.config.logging_manager import LoggingManager
from websrc.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="websrc/templates")
logging_manager = LoggingManager()
@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Serve Landing Page",
    description="Serves the landing page.",
)
async def serve_landing(request: Request):
    """Serve the landing page"""
    return templates.TemplateResponse(
        "landing.html",
        {"request": request}
    )

@router.get(
    "/home",
    response_class=HTMLResponse,
    summary="Serve Home Page",
    description="Serves the main chat interface.",
)
@logging_manager.log_and_trace("serve_home")
async def serve_home(request: Request):
    """Serve the main chat interface"""
    text_model_names = [name.display_name for name in TextRepoName]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "text_model_names": text_model_names,
            "model_name": settings.GENMODEL_NAME,
            "page_type": "Home",
            "settings": settings
        }
    )

@router.get(
    "/settings",
    response_class=HTMLResponse,
    summary="Serve Settings Page",
    description="Serves the settings page.",
)
@logging_manager.log_and_trace("serve_settings")
async def serve_settings(request: Request):
    """Serve the settings page"""
    text_model_names = [name.display_name for name in TextRepoName]
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "text_model_names": text_model_names,
            "model_name": settings.GENMODEL_NAME,
        }
    )

@router.get(
    "/api",
    response_class=HTMLResponse,
    summary="Serve API Page",
    description="Serves the API documentation page.",
)
@logging_manager.log_and_trace("serve_api")
async def serve_api(request: Request):
    """Serve the API documentation page"""
    return templates.TemplateResponse(
        "api.html",
        {"request": request}
    )
    
@router.get(
    "/models",
    response_class=HTMLResponse,
    summary="Serve Models Page",
    description="Serves the models page.",
)
async def serve_models(request: Request):
    """Serve the models page"""
    return templates.TemplateResponse(
        "models.html",
        {"request": request}
    )