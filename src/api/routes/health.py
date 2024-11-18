from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get(
    "/health/",
    response_class=JSONResponse,
    summary="Health Check", 
    description="Returns the health status of the application.",
    tags=["Health"],
)
async def health_check():
    """Health check endpoint to verify the application is running."""
    return {"status": "ok"}