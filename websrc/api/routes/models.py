from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from src.dependencies.container import ModelDiscoveryServiceDependency, SystemInfoDependency
from websrc.models.pydantic import ModelDownloadRequest, ModelDeleteRequest, ModelSelectRequest
from src.models.enum import ModelType
from websrc.config.logging_manager import LoggingManager

router = APIRouter()
logging_manager = LoggingManager()

@router.get(
    "/api/system/info",
    response_class=JSONResponse,
    summary="Get System Info",
    description="Gets system capabilities and specifications.",
    tags=["Models"],
)
@logging_manager.log_and_trace("get_system_info")
async def get_system_info(
    system_info: SystemInfoDependency
) -> Dict[str, Any]:
    """Get system capabilities"""
    return system_info.get_capabilities().__dict__

@router.get(
    "/api/models/{model_type}",
    response_class=JSONResponse,
    summary="Get Models",
    description="Gets available models by type.",
    tags=["Models"],
)
@logging_manager.log_and_trace("get_models")
async def get_models(
    model_type: ModelType,
    model_service: ModelDiscoveryServiceDependency
) -> List[Dict[str, Any]]:
    """Get available models by type"""
    try:
        models = await model_service.get_available_models(model_type)
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/models/download",
    response_class=JSONResponse,
    summary="Download Model",
    description="Downloads a model for local use.",
    tags=["Models"],
)
@logging_manager.log_and_trace("download_model")
async def download_model(
    request: ModelDownloadRequest,
    model_service: ModelDiscoveryServiceDependency
):
    """Download a model"""
    try:
        await model_service.download_model(request.model_id, ModelType(request.type))
        return JSONResponse({"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/models/delete",
    response_class=JSONResponse,
    summary="Delete Model",
    description="Deletes a downloaded model.",
    tags=["Models"],
)
@logging_manager.log_and_trace("delete_model")
async def delete_model(
    request: ModelDeleteRequest,
    model_service: ModelDiscoveryServiceDependency
):
    """Delete a downloaded model"""
    try:
        await model_service.delete_model(request.model_id, ModelType(request.type))
        return JSONResponse({"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/models/select",
    response_class=JSONResponse,
    summary="Select Model",
    description="Selects a model as current for its type.",
    tags=["Models"],
)
@logging_manager.log_and_trace("select_model")
async def select_model(
    request: ModelSelectRequest,
    model_service: ModelDiscoveryServiceDependency
):
    """Select a model as current"""
    try:
        await model_service.select_model(request.model_id, ModelType(request.type))
        return JSONResponse({"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/models/current/{model_type}",
    response_class=JSONResponse,
    summary="Get Current Model",
    description="Gets currently selected model for type.",
    tags=["Models"],
)
@logging_manager.log_and_trace("get_current_model")
async def get_current_model(
    model_type: str,
    model_service: ModelDiscoveryServiceDependency
):
    """Get currently selected model for type"""
    try:
        current = await model_service.get_current_model(ModelType(model_type))
        return JSONResponse({"model_id": current.id if current else None})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
