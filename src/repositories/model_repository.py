from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy import select, delete
from src.db.unit_of_work import UnitOfWork
from src.models.enum import ModelType
from src.models.database import ModelInfo
from src.repositories.base_repository import BaseRepository, transaction
from exceptions.exceptions import NotFoundError

class ModelRepository(BaseRepository[ModelInfo]):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, ModelInfo)

    async def get_active_model(self, model_type: ModelType) -> Optional[ModelInfo]:
        query = select(ModelInfo).where(
            ModelInfo.type == model_type,
            ModelInfo.is_active == True
        )
        result = await self.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, model_id: str) -> Optional[ModelInfo]:
        query = select(ModelInfo).where(ModelInfo.model_id == model_id)
        result = await self.execute(query)
        return result.scalar_one_or_none()

    async def delete_by_id(self, model_id: str) -> None:
        result = await self.get_by_id(model_id)
        if result:
            await self.delete(result)
        else:
            raise NotFoundError(f"Model with id {model_id} not found", self.__class__.__name__)

    async def set_active(self, model_id: str, model_type: ModelType) -> None:
        current_active = await self.get_active_model(model_type)
        if current_active:
            current_active.is_active = False