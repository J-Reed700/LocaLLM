from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.enum import ModelType
from src.models.database import LocalModel
from src.db.unit_of_work import UnitOfWork
from src.repositories.base_repository import BaseRepository
from sqlalchemy import select

class ModelRepository(BaseRepository[LocalModel]):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, LocalModel)

    async def get_by_id(self, model_id: str) -> Optional[LocalModel]:
        query = select(LocalModel).where(LocalModel.model_id == model_id)
        result = await self.uow.execute(query)
        return result.scalar_one_or_none()

    async def get_active_model(self, model_type: ModelType) -> Optional[LocalModel]:
        query = select(LocalModel).where(
            LocalModel.type == model_type,
            LocalModel.is_active == True
        )
        result = await self.uow.execute(query)
        return result.scalar_one_or_none()

    async def set_active(self, model_id: str, model_type: ModelType) -> None:
        current_active = await self.get_active_model(model_type)
        if current_active:
            current_active.is_active = False 