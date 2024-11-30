from typing import Optional, Any, Dict, Type, List
from src.services.database_context import DatabaseContext
from src.models.database import SettingScope, SettingKey
from src.models.dto import SettingDTO
from src.models.pydantic import SettingCreate, SettingUpdate
from src.services.settings.value_handler import SettingValueHandler
from exceptions.exceptions import NotFoundError
from websrc.config.settings import settings
from functools import lru_cache


class SettingsService():
    def __init__(self, db_context: DatabaseContext, value_handler: SettingValueHandler):
        self.db_context = db_context
        self.value_handler = value_handler
        self._default_system_prompt = None

    @lru_cache(maxsize=1)
    async def get_default_system_prompt(self) -> str:
        """Get cached default system prompt"""
        if self._default_system_prompt is None:
            setting = await self.get_setting(
                SettingKey.SYSTEM_PROMPT,
                SettingScope.GLOBAL
            )
            self._default_system_prompt = setting.value if setting else "You are a helpful AI assistant."
        return self._default_system_prompt

    async def invalidate_system_prompt_cache(self):
        """Invalidate the system prompt cache when settings are updated"""
        self._default_system_prompt = None
        self.get_default_system_prompt.cache_clear()

    async def get_setting(
        self, 
        key: SettingKey, 
        scope: SettingScope, 
        scope_id: Optional[int] = None
    ) -> Optional[SettingDTO]:
        setting = await self.db_context.settings.get_setting(key, scope, scope_id)
        if not setting:
            return None
        return SettingDTO.from_db_model(setting)

    async def create_setting(self, data: SettingCreate) -> SettingDTO:
        # Validate and convert the value
        processed_value = self.value_handler.validate_and_convert(data.value, data.value_type)
        
        setting_dto = SettingDTO(
            key=data.key,
            value=processed_value,
            value_type=data.value_type,
            scope=data.scope,
            scope_id=data.scope_id
        )
        
        db_setting = await self.db_context.settings.create_setting(setting_dto)
        return SettingDTO.from_db_model(db_setting)

    async def upsert_setting(
        self,
        key: str,
        scope: SettingScope,
        data: SettingUpdate,
        scope_id: Optional[int] = None
    ) -> SettingDTO:
        
        setting = SettingDTO(
            key=key,
            scope=scope,
            scope_id=scope_id,
            value=data.value,
            value_type=data.value_type
        )

        processed_value = self.value_handler.validate_and_convert(
            setting.value, 
            setting.value_type
        )

        setting.value = processed_value
        db_setting = await self.db_context.settings.upsert_setting(setting)
        
        if key == SettingKey.SYSTEM_PROMPT and scope == SettingScope.CHAT:
            await self.invalidate_system_prompt_cache()
        
        return SettingDTO.from_db_model(db_setting)

    async def get_settings_by_scope(self, scope: SettingScope, scope_id: Optional[int] = None) -> List[SettingDTO]:
        settings = await self.db_context.settings.get_settings_by_scope(scope, scope_id)
        return [SettingDTO.from_db_model(setting) for setting in settings]

    async def delete_setting(self, key: str, scope: SettingScope, scope_id: Optional[int] = None) -> None:
        await self.db_context.settings.delete_setting(key, scope, scope_id)
    # High-level business methods
    async def get_api_settings(self, api_id: Optional[int] = None) -> List[SettingDTO]:
        return await self.get_settings_by_scope(SettingScope.API, api_id)

    async def get_chat_settings(self, chat_id: int) -> List[SettingDTO]:
        return await self.get_settings_by_scope(SettingScope.CHAT, chat_id)

    async def get_global_settings(self) -> List[SettingDTO]:
        return await self.get_settings_by_scope(SettingScope.GLOBAL)

    async def update_settings_batch(self, settings: Dict[str, Any], scope: SettingScope, scope_id: Optional[int] = None) -> List[SettingDTO]:
        results = []
        for key, value in settings.items():
            setting = await self.update_setting(
                key,
                scope,
                SettingUpdate(value=value),
                scope_id
            )
            results.append(setting)
        return results

    async def get_default_chat_settings(self) -> Dict[str, Any]:
        return {
            SettingKey.MODEL_NAME: settings.CHAT_DEFAULT_MODEL,
            SettingKey.MAX_LENGTH: settings.CHAT_MAX_LENGTH,
            SettingKey.TEMPERATURE: settings.CHAT_TEMPERATURE,
            SettingKey.TOP_P: settings.CHAT_TOP_P,
            SettingKey.TOP_K: settings.CHAT_TOP_K,
            SettingKey.REPETITION_PENALTY: settings.CHAT_REPETITION_PENALTY,
            SettingKey.SYSTEM_PROMPT: settings.CHAT_DEFAULT_SYSTEM_PROMPT
        }
