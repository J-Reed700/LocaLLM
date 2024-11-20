from typing import Optional, AsyncGenerator
from fastapi import Depends
from src.services.llm_generate import LLMGenerate, ModelFactory
from websrc.config.settings import settings
from src.services.database import DatabaseService
from src.db.session import AsyncSessionLocal
import logging

class ServiceContainer:
    def __init__(self):
        self._factory: Optional[ModelFactory] = None
        self._llm_service: Optional[LLMGenerate] = None
        self._db_service: Optional[DatabaseService] = None
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
    def db_service(self) -> DatabaseService:
        if not self._db_service:
            self._db_service = DatabaseService(AsyncSessionLocal)
        return self._db_service

    async def get_model_factory(self) -> ModelFactory:
        return self.factory

    async def get_llm_generate_service(
        self,
        factory: ModelFactory = Depends(get_model_factory)
    ) -> AsyncGenerator[Optional[LLMGenerate], None]:
        try:
            yield self.llm_service
        except Exception as e:
            self.logger.error(f"LLM service error: {e}")
            yield None

    async def get_db_service(self) -> AsyncGenerator[DatabaseService, None]:
        try:
            yield self.db_service
        except Exception as e:
            self.logger.error(f"Database service error: {e}")
            yield None

container = ServiceContainer() 