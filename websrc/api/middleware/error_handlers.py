import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from exceptions.exceptions import BaseAppError
from exceptions.exceptions import (
    InvalidModelTypeError,
    InvalidModelNameError,
    ModelConfigurationError,
    ModelLoadingError,
    TextGenerationError,
    ImageGenerationError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    TextGenerationValidationError,
    RequestValidationError
)
from fastapi.exceptions import RequestValidationError as FastAPIValidationError
from pydantic import ValidationError as PydanticValidationError
from typing import Any, Dict, List
import traceback
import sys
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from datetime import datetime

logger = logging.getLogger(__name__)

# Mapping of exception classes to their HTTP status codes and messages
exception_mapping = {
    InvalidModelTypeError: {"status_code": 400, "detail": "Invalid model type provided."},
    InvalidModelNameError: {"status_code": 400, "detail": "Invalid model name provided."},
    ModelConfigurationError: {"status_code": 400, "detail": "Model configuration error."},
    ModelLoadingError: {"status_code": 500, "detail": "Failed to load the model."},
    TextGenerationError: {"status_code": 500, "detail": "Text generation failed."},
    ImageGenerationError: {"status_code": 500, "detail": "Image generation failed."},
    DatabaseError: {"status_code": 503, "detail": "Database service unavailable."},
    ValidationError: {"status_code": 422, "detail": "Validation error."},
    AuthenticationError: {"status_code": 401, "detail": "Authentication required."},
    AuthorizationError: {"status_code": 403, "detail": "Access forbidden."},
    NotFoundError: {"status_code": 404, "detail": "Resource not found."},
    ConflictError: {"status_code": 409, "detail": "Conflict error."},
    RateLimitError: {"status_code": 429, "detail": "Rate limit exceeded."},
    TextGenerationValidationError: {
        "status_code": 422, 
        "detail": "Text generation validation failed."
    }
}

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors"""
    span = trace.get_current_span()
    span.set_status(Status(StatusCode.ERROR))
    span.record_exception(exc)
    
    logger.error(f"Validation error: {str(exc)}")
    
    errors = [{
        "field": error.get("loc", ["unknown"])[-1],
        "message": error.get("msg"),
        "type": error.get("type")
    } for error in exc.errors()]
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": errors
            }
        }
    )

async def base_app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    """Handle application-specific errors"""
    span = trace.get_current_span()
    trace_id = span.get_span_context().trace_id
    
    error_info = exception_mapping.get(type(exc), {
        "status_code": 500,
        "detail": "An unexpected error occurred"
    })
    
    logger.error(
        f"Application error occurred",
        extra={
            "trace_id": trace_id,
            "error_type": exc.__class__.__name__,
            "error_message": exc.message,
            "path": request.url.path
        }
    )
    
    response_data = {
        "status": "error",
        "code": error_info["status_code"],
        "message": exc.message or error_info["detail"],
        "type": exc.__class__.__name__,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "trace_id": trace_id
    }
    
    if hasattr(exc, 'errors'):
        response_data["details"] = exc.errors
    
    return JSONResponse(
        status_code=error_info["status_code"],
        content=response_data
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "type": "UnexpectedError",
                "message": "An unexpected error occurred"
            }
        }
    )