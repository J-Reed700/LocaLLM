from src.repositories.base_repository import BaseRepository, transaction
from src.models.database import Setting
from src.models.dto import SettingDTO
from src.models.database import SettingScope, SettingKey
from src.db.unit_of_work import UnitOfWork
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import select


class SettingsRepository(BaseRepository[Setting]):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, Setting)
    
    async def get_setting(self, key: SettingKey, scope: SettingScope, scope_id: Optional[int] = None) -> Optional[Setting]:
        query = select(Setting).where(
            Setting.key == key,
            Setting.scope == scope,
            Setting.scope_id == scope_id
        )
        result = await self.uow.execute(query)
        return result.scalar_one_or_none()

    @transaction
    async def create_setting(self, setting_dto: SettingDTO) -> Setting:
        db_setting = setting_dto.to_db_model()
        return await self.uow.add_with_retry(db_setting)
        
    @transaction
    async def upsert_setting(self, setting_dto: SettingDTO) -> Setting:
        existing = await self.get_setting(
            setting_dto.key, 
            setting_dto.scope, 
            setting_dto.scope_id
        ) or setting_dto.to_db_model()
        
        self._set_timestamps(existing)
        return await self.uow.add(existing)

    async def get_settings_by_scope(self, scope: SettingScope, scope_id: Optional[int] = None) -> List[Setting]:
        conditions = [Setting.scope == scope]
        if scope_id is not None:
            conditions.append(Setting.scope_id == scope_id)
        
        query = select(Setting).where(*conditions)
        result = await self.uow.execute(query)
        return list(result.scalars().all())

    @transaction
    async def delete_setting(self, key: str, scope: SettingScope, scope_id: Optional[int] = None) -> None:
        setting = await self.get_setting(key, scope, scope_id)
        if setting:
            await self.uow.delete_with_retry(setting) 