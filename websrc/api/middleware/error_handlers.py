import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from websrc.api.exceptions.exceptions import BaseAppError
from websrc.api.exceptions.exceptions import (
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

def format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format validation errors into a consistent structure"""
    formatted_errors = []
    for error in errors:
        formatted_errors.append({
            "field": error.get("loc", ["unknown"])[-1],
            "message": error.get("msg"),
            "type": error.get("type")
        })
    return formatted_errors

async def validation_exception_handler(request: Request, exc: FastAPIValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors"""
    span = trace.get_current_span()
    span.set_status(Status(StatusCode.ERROR))
    span.record_exception(exc)
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": format_validation_errors(exc.errors())
            }
        }
    )

async def base_app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    """Enhanced global exception handler for BaseAppError and its subclasses"""
    logger.error(
        f"Application error: {exc.__class__.__name__}",
        extra={
            "error_type": exc.__class__.__name__,
            "error_message": exc.message,
            "status_code": exc.code,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exception(*sys.exc_info())
        }
    )
    
    response_data = {
        "status": "error",
        "error": {
            "type": exc.__class__.__name__,
            "message": exc.message,
            "code": exc.code
        }
    }
    
    # Add additional error details for specific error types
    if isinstance(exc, RequestValidationError):
        response_data["error"]["details"] = exc.errors
    
    if isinstance(exc, DatabaseError):
        response_data["error"]["retry_after"] = 30  # Suggest retry after 30 seconds
    
    # Add validation error details
    if isinstance(exc, TextGenerationValidationError):
        response_data["error"]["details"] = format_validation_errors(exc.errors)
    
    return JSONResponse(
        status_code=exc.code,
        content=response_data
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected exceptions"""
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