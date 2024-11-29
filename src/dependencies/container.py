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

# Service dependencies with proper async context management
async def get_conversation_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)]
) -> ConversationService:
    return ConversationService(db)

async def get_message_service(
    db: Annotated[DatabaseContext, Depends(get_db_context)]
) -> MessageService:
    return MessageService(db)

async def get_llm_service(
    conversation_service: Annotated[ConversationService, Depends(get_conversation_service)],
    message_service: Annotated[MessageService, Depends(get_message_service)]
) -> LLMGenerate:
    if not settings.ENABLE_LLM_SERVICE:
        raise ModelLoadingError("LLM service is not enabled")
    conversation_context = ConversationContext(
        conversation_service=conversation_service,
        message_service=message_service
    )
    return LLMGenerate(get_model_factory(), conversation_context)

# Type aliases for cleaner dependency injection
LLMDependency = Annotated[LLMGenerate, Depends(get_llm_service)]
ConversationServiceDependency = Annotated[ConversationService, Depends(get_conversation_service)]
MessageServiceDependency = Annotated[MessageService, Depends(get_message_service)]