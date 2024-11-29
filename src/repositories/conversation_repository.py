from src.repositories.base_repository import BaseRepository
from src.models.database import Conversation
from src.db.unit_of_work import UnitOfWork
from src.repositories.interfaces import IConversationRepository
from typing import Optional, List
from websrc.api.exceptions.exceptions import NotFoundError

class ConversationRepository(BaseRepository[Conversation], IConversationRepository):
    def __init__(self, unit_of_work: UnitOfWork):
        super().__init__(unit_of_work, Conversation)

    async def save(self, conversation: Conversation) -> Conversation:
        async with self.uow.transaction():
            return await self.add(conversation)
    
    async def update(self, conversation: Conversation) -> Conversation:
        async with self.uow.transaction():
            return await self.add(conversation)

    async def get_by_id(self, id: int) -> Optional[Conversation]:
        return await self.get(id)
        
    async def list_all(self) -> List[Conversation]:
        return await self.list()

    async def delete_by_id(self, id: int) -> None:
        async with self.uow.transaction():
            conversation = await self.get_by_id(id)
            if conversation:
                await self.delete(conversation)
            
    async def add_category(self, conversation: Conversation, category) -> None:
        async with self.uow.transaction():
            conversation.categories.append(category)
            await self.update(conversation)