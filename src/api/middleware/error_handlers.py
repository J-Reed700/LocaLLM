import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from src.api.exceptions.exceptions import BaseAppError

logger = logging.getLogger(__name__)

async def base_app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    """Global exception handler for BaseAppError and its subclasses"""
    logger.error(f"{exc.__class__.__name__}: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )