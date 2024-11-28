from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from websrc.config.logging_config import log_endpoint, track_span_exceptions

router = APIRouter()

@router.get(
    "/health/",
    response_class=JSONResponse,
    summary="Health Check", 
    description="Returns the health status of the application.",
    tags=["Health"],
)
@log_endpoint
@track_span_exceptions()
async def health_check():
    """Health check endpoint to verify the application is running."""
    return JSONResponse({"status": "healthy"})