from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional
from src.models.pydantic import SettingCreate, SettingUpdate, SettingResponse
from src.models.database import SettingScope
from src.services.settings_service import SettingsService
from src.dependencies.container import SettingsServiceDependency
from websrc.config.logging_manager import LoggingManager

router = APIRouter()
logging_manager = LoggingManager()

@router.get(
    "/settings/{scope}",
    response_model=List[SettingResponse],
    summary="Get Settings by Scope",
    description="Gets all settings for a given scope.",
    tags=["Settings"]
)
@logging_manager.log_and_trace("get_settings") 
async def get_settings(
    settings_service: SettingsServiceDependency,
    scope: str = Path(..., description="Setting scope"),
    scope_id: Optional[int] = None
) -> List[SettingResponse]:
    try:
        enum_scope = SettingScope(scope.lower())
        settings = await settings_service.get_settings_by_scope(enum_scope, scope_id)
        return [SettingResponse(**setting.model_dump()) for setting in settings]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope. Must be one of: {[e.value for e in SettingScope]}"
        )

@router.get(
    "/settings/{scope}/{key}",
    response_model=SettingResponse,
    summary="Get Setting",
    description="Gets a specific setting by scope and key.",
    tags=["Settings"]
)
@logging_manager.log_and_trace("get_setting")
async def get_setting(
    settings_service: SettingsServiceDependency,
    scope: str = Path(..., description="Setting scope"),
    key: str = Path(..., description="Setting key"),
    scope_id: Optional[int] = None
) -> SettingResponse:
    enum_scope = SettingScope(scope.lower())
    setting = await settings_service.get_setting(key, enum_scope, scope_id)
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting {key} not found")
    return SettingResponse(**setting.model_dump())

@router.post(
    "/settings",
    response_model=SettingResponse,
    summary="Create Setting",
    description="Creates a new setting.",
    tags=["Settings"]
)
@logging_manager.log_and_trace("create_setting")
async def create_setting(
    data: SettingCreate,
    settings_service: SettingsServiceDependency
) -> SettingResponse:
    setting = await settings_service.create_setting(data)
    return SettingResponse(**setting.model_dump())

@router.put(
    "/settings/{scope}/{key}",
    response_model=SettingResponse,
    summary="Update Setting",
    description="Updates an existing setting or creates if not found.",
    tags=["Settings"]
)
@logging_manager.log_and_trace("upsert_setting")
async def upsert_setting(
    scope: SettingScope,
    key: str,
    data: SettingUpdate,
    settings_service: SettingsServiceDependency,
    scope_id: Optional[int] = None
) -> SettingResponse:
    setting = await settings_service.upsert_setting(key, scope, data, scope_id)
    return SettingResponse(**setting.model_dump())

@router.delete(
    "/settings/{scope}/{key}",
    summary="Delete Setting",
    description="Deletes a setting.",
    tags=["Settings"]
)
@logging_manager.log_and_trace("delete_setting")
async def delete_setting(
    scope: SettingScope,
    key: str,
    settings_service: SettingsServiceDependency,
    scope_id: Optional[int] = None
):
    await settings_service.delete_setting(key, scope, scope_id)
    return {"message": "Setting deleted successfully"}
