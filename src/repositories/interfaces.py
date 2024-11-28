from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from src.models.database import Conversation, Message

class IConversationRepository(ABC):
    @abstractmethod
    async def add_category(self, conversation: Conversation, category) -> None:
        pass

class IMessageRepository(ABC):
    @abstractmethod
    async def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        pass 