from typing import Optional
from fastapi import Depends
from websrc.services.llm_generate import LLMGenerate, ModelFactory

def get_model_factory() -> ModelFactory:
    return ModelFactory()

def get_llm_generate_service(factory: ModelFactory = Depends(get_model_factory)) -> Optional[LLMGenerate]:
    try:
        return factory.create_service()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create LLMGenerate service: {e}")
        return None 