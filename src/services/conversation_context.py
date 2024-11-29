from typing import List, Optional, Tuple
from src.models.dto import MessageDTO, ConversationDTO
from src.services.message_service import MessageService
from src.services.conversation_service import ConversationService
from src.models.pydantic import MessageCreate, ConversationCreate
from src.models.pydantic import TextGeneration
from exceptions.exceptions import NotFoundError

class ConversationContext:
    def __init__(self, 
                 conversation_service: ConversationService,
                 message_service: MessageService):
        self.conversation_service = conversation_service
        self.message_service = message_service
        
    async def process_request(self, request: TextGeneration) -> Tuple[ConversationDTO, MessageDTO]:
        """Process a conversation request, creating new conversation if needed"""
        if request.conversation_id is None:
            conversation = await self.create_conversation(request.model_type, request.model_name)
        else:
            conversation = await self.conversation_service.get(request.conversation_id)
            
        # Add user message
        user_message = await self.add_message(
            conversation.id,
            content=request.prompt,
            role="user"
        )
        
        return conversation, user_message
        
    async def create_conversation(self, model_type: str, model_name: str) -> ConversationDTO:
        conversation = await self.conversation_service.create(
            ConversationCreate(
                title="New Conversation",
                type=model_type,
                name=model_name
            )
        )
        return conversation
        
    async def get_conversation_history(self, conversation_id: int, before_message_id: Optional[int] = None) -> List[MessageDTO]:
        try:
            messages = await self.message_service.list_by_conversation(conversation_id, before_message_id)
            return messages
        except NotFoundError:
            return []
            
    async def add_message(self, conversation_id: int, content: str, role: str) -> MessageDTO:
        message = await self.message_service.create(
            conversation_id=conversation_id,
            data=MessageCreate(
                role=role,
                content=content
            )
        )
        if not message or not message.id:
            raise ValueError("Failed to add message: Database did not return ID")
        return message

    def format_context(self, messages: List[MessageDTO]) -> str:
        """Format conversation history for LLM context"""
        formatted_messages = []
        for msg in messages:
            role_prefix = "User: " if msg.role == "user" else "Assistant: "
            formatted_messages.append(f"{role_prefix}{msg.content}")
        return "\n".join(formatted_messages) 