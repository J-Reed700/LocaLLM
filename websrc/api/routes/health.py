from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from websrc.config.logging_manager import LoggingManager

router = APIRouter()
logging_manager = LoggingManager()

@router.get(
    "/health/",
    response_class=JSONResponse,
    summary="Health Check", 
    description="Returns the health status of the application.",
    tags=["Health"],
)   
@logging_manager.log_and_trace("health_check")
async def health_check():
    """Health check endpoint to verify the application is running."""
    return JSONResponse({"status": "healthy"}) 