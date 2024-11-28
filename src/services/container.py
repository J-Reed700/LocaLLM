from typing import Optional, AsyncGenerator
from fastapi import Depends
from src.services.llm_generate import LLMGenerate, ModelFactory
from websrc.config.settings import settings
from src.services.database_context import DatabaseContext
from src.services.conversation_service import ConversationService
from src.db.session import AsyncSessionLocal, engine
from websrc.api.exceptions.exceptions import ModelLoadingError, DatabaseError
from src.services.message_service import MessageService
import logging

class ServiceContainer:
    def __init__(self):
        self._factory: Optional[ModelFactory] = None
        self._llm_service: Optional[LLMGenerate] = None
        self._conversation_service: Optional[ConversationService] = None
        self._message_service: Optional[MessageService] = None
        self.logger = logging.getLogger(__name__)
    
    @property
    def factory(self) -> ModelFactory:
        if not self._factory:
            self._factory = ModelFactory()
        return self._factory
    
    @property
    def llm_service(self) -> Optional[LLMGenerate]:
        if not self._llm_service and settings.ENABLE_LLM_SERVICE:
            self._llm_service = LLMGenerate(self.factory)
        return self._llm_service

    @property
    def conversation_service(self) -> ConversationService:
        if not self._conversation_service:
            self._conversation_service = ConversationService(DatabaseContext(AsyncSessionLocal))
        return self._conversation_service

    @property
    def message_service(self) -> MessageService:
        if not self._message_service:
            self._message_service = MessageService(DatabaseContext(AsyncSessionLocal))
        return self._message_service

    async def get_model_factory(self) -> ModelFactory:
        return self.factory

    async def get_llm_generate_service(
        self
    ) -> AsyncGenerator[LLMGenerate, None]:
        try:
            yield self.llm_service
        except Exception as e:
            self.logger.error(f"LLM service error: {e}")
            raise ModelLoadingError(f"LLM service error: {str(e)}")
        
    async def get_conversation_service(self) -> AsyncGenerator[ConversationService, None]:
        try:
            yield self.conversation_service
        except Exception as e:
            self.logger.error(f"Conversation service error: {e}")
            raise DatabaseError(f"Conversation service error: {str(e)}")

    async def get_message_service(self) -> AsyncGenerator[MessageService, None]:
        try:
            yield self.message_service
        except Exception as e:
            self.logger.error(f"Message service error: {e}")
            raise DatabaseError(f"Message service error: {str(e)}")

container = ServiceContainer() 

async def get_llm_generate_service_dependency(
    llm_service: LLMGenerate = Depends(container.get_llm_generate_service)
) -> LLMGenerate:
    return llm_service

async def get_conversation_service_dependency(
    conversation_service: ConversationService = Depends(container.get_conversation_service)
) -> ConversationService:
    return conversation_service

async def get_message_service_dependency(
    message_service: MessageService = Depends(container.get_message_service)
) -> MessageService:
    return message_service