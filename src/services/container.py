from functools import lru_cache
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from src.services.llm_generate import LLMGenerate, ModelFactory
from websrc.config.settings import settings
from src.services.database_context import DatabaseContext
from src.services.conversation_service import ConversationService
from src.db.session import AsyncSessionLocal
from websrc.api.exceptions.exceptions import ModelLoadingError, DatabaseError
from src.services.message_service import MessageService
from typing import AsyncIterator

# Create singleton instances using lru_cache
@lru_cache
def get_model_factory() -> ModelFactory:
    return ModelFactory()

@lru_cache
def get_llm_service() -> LLMGenerate | None:
    if not settings.ENABLE_LLM_SERVICE:
        return None
    return LLMGenerate(get_model_factory())

# Database context manager
@asynccontextmanager
async def get_db() -> AsyncIterator[DatabaseContext]:
    context = DatabaseContext(AsyncSessionLocal)
    try:
        yield context
    finally:
        await context.close()  

# Dependencies
async def get_db_context() -> AsyncGenerator[DatabaseContext, None]:
    async with get_db() as db:
        yield db

async def get_llm_generate() -> AsyncGenerator[LLMGenerate, None]:
    llm = get_llm_service()
    if not llm:
        raise ModelLoadingError("LLM service is not enabled")
    yield llm

# Type aliases for cleaner dependency injection
DatabaseContextDependency = Annotated[DatabaseContext, Depends(get_db_context)]
LLMDependency = Annotated[LLMGenerate, Depends(get_llm_generate)]

# Service dependencies
async def get_conversation_service(db: DatabaseContextDependency) -> ConversationService:
    return ConversationService(db)

async def get_message_service(db: DatabaseContextDependency) -> MessageService:
    return MessageService(db)

# Type aliases for service dependencies
ConversationServiceDependency = Annotated[ConversationService, Depends(get_conversation_service)]
MessageServiceDependency = Annotated[MessageService, Depends(get_message_service)]

