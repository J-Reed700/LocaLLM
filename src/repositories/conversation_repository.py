from src.repositories.base_repository import BaseRepository, transaction, transaction_with_retry
from src.models.database import Conversation
from src.db.unit_of_work import UnitOfWork
from typing import Optional, List
from sqlalchemy import select
from exceptions.exceptions import NotFoundError

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, Conversation)

    async def get_by_id(self, id: int) -> Optional[Conversation]:
        query = select(Conversation).where(Conversation.id == id)
        result = await self.uow.execute(query)
        return result.scalars().first()

    async def list_all(self, order_by: str = "created_at", order_direction: str = "asc") -> List[Conversation]:
        query = select(Conversation)
        if order_by == "created_at":
            query = query.order_by(
                Conversation.created_at.desc() if order_direction == "desc" 
                else Conversation.created_at.asc()
            )
        result = await self.execute(query)
        return result.scalars().all()

    async def add_category(self, conversation: Conversation, category) -> None:
        conversation.categories.append(category)
        await self.add_with_retry(conversation)

    async def update_with_retry(self, conversation: Conversation) -> Conversation:
        conversation = await self.add_with_retry(conversation)
        return conversation

    async def delete_by_id(self, id: int) -> None:
        conversation = await self.get_by_id(id)
        if conversation:
            await self.delete(conversation)

    async def delete_by_id_with_retry(self, id: int) -> None:
        conversation = await self.get_by_id(id)
        if conversation:
            await self.delete_with_retry(conversation)
        raise NotFoundError(f"Conversation with id {id} not found", self.__class__.__name__)