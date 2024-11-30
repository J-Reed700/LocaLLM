from functools import lru_cache
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from src.services.llm_generate import LLMGenerate, ModelFactory
from websrc.config.settings import settings
from src.services.database_context import DatabaseContext
from src.services.conversation_service import ConversationService
from src.db.session import AsyncSessionLocal
from exceptions.exceptions import ModelLoadingError
from src.services.message_service import MessageService
from src.services.conversation_context import ConversationContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.settings.value_handler import SettingValueHandler
from src.services.settings_service import SettingsService
from src.services.model_discovery import ModelDiscoveryService
from src.services.storage_service import SecureStorageService
from src.utils.system_capabilities import SystemInfo
@lru_cache
def get_model_factory() -> ModelFactory:
    return ModelFactory()

async def get_db_context() -> AsyncGenerator[DatabaseContext, None]:
    db = DatabaseContext(AsyncSessionLocal)
    try:
        async with db as context:
            yield context
    finally:
        await db.close()

async def get_system_info() -> SystemInfo:
    return SystemInfo()

SystemInfoDependency = Annotated[SystemInfo, Depends(get_system_info)]
# Service dependencies with proper async context management
async def get_conversation_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)]
) -> ConversationService:
    return ConversationService(db)

async def get_message_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)]
) -> MessageService:
    return MessageService(db)

async def get_secure_storage_service() -> SecureStorageService:
    return SecureStorageService()

async def get_model_discovery_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)],
    storage: Annotated[SecureStorageService, Depends(get_secure_storage_service)]
) -> ModelDiscoveryService:
    return ModelDiscoveryService(db, storage)

async def get_settings_handler() -> SettingValueHandler:
    return SettingValueHandler()

async def get_settings_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)],
    value_handler: Annotated[SettingValueHandler, Depends(get_settings_handler)]
) -> SettingsService:
    return SettingsService(db, value_handler)

ConversationServiceDependency = Annotated[ConversationService, Depends(get_conversation_service)]
MessageServiceDependency = Annotated[MessageService, Depends(get_message_service)]
SettingsServiceDependency = Annotated[SettingsService, Depends(get_settings_service)]
ModelDiscoveryServiceDependency = Annotated[ModelDiscoveryService, Depends(get_model_discovery_service)]

async def get_conversation_context(
    conversation_service: ConversationServiceDependency,
    message_service: MessageServiceDependency
) -> ConversationContext:
    return ConversationContext(conversation_service, message_service)

ConversationContextDependency = Annotated[ConversationContext, Depends(get_conversation_context)]

async def get_llm_service(
    conversation_context: ConversationContextDependency,
    settings_service: SettingsServiceDependency
) -> LLMGenerate:
    return LLMGenerate(get_model_factory(), conversation_context, settings_service)

# Type aliases for cleaner dependency injection
LLMDependency = Annotated[LLMGenerate, Depends(get_llm_service)]
