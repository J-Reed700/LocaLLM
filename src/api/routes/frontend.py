from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
import logging
import jinja2
from src.models.pydantic import TextModelName
from fastapi.templating import Jinja2Templates
import os
from src.config.logging_config import log_async_function


router = APIRouter()
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory= "src/templates")

@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Serve Frontend",
    description="Serves the HTMX home page.",
)
@log_async_function
async def serve_frontend(request: Request):
    """Serve the HTMX frontend interface"""
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