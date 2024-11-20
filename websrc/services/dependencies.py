from typing import Optional, AsyncGenerator
from fastapi import Depends
from contextlib import asynccontextmanager
from websrc.services.llm_generate import LLMGenerate, ModelFactory
from websrc.config.settings import settings

class ServiceContainer:
    def __init__(self):
        self._factory: Optional[ModelFactory] = None
        self._llm_service: Optional[LLMGenerate] = None
    
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

container = ServiceContainer()

async def get_model_factory() -> ModelFactory:
    return container.factory

async def get_llm_generate_service(
    factory: ModelFactory = Depends(get_model_factory)
) -> AsyncGenerator[Optional[LLMGenerate], None]:
    try:
        yield container.llm_service
    except Exception as e:
        logging.getLogger(__name__).error(f"LLM service error: {e}")
        yield None 