from src.repositories.base_repository import BaseRepository
from src.models.database import Conversation, ModelType
from sqlalchemy.ext.asyncio import AsyncSession

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def add_category(self, conversation: Conversation, category) -> None:
        conversation.categories.append(category)
        await self.update(conversation)

    async def remove_category(self, conversation: Conversation, category) -> None:
        conversation.categories.remove(category)
        await self.update(conversation)

    # Add more conversation-specific manipulations here 