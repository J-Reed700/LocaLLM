from typing import List, Optional, Tuple
from src.models.dto import MessageDTO, ConversationDTO
from src.services.message_service import MessageService
from src.services.conversation_service import ConversationService
from src.models.pydantic import MessageCreate, ConversationCreate, ModelParameters
from src.models.pydantic import TextGeneration, ModelType
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
            conversation = await self.create_conversation(request.parameters.type, request.parameters.name, request.prompt)
        else:
            conversation = await self.conversation_service.get(request.conversation_id)
            
        # Add user message
        user_message = await self.add_message(
            conversation.id,
            content=request.prompt,
            role="user"
        )
        
        return conversation, user_message
        
    async def create_conversation(self, model_type: ModelType, model_name: str, system_prompt: Optional[str] = None) -> ConversationDTO:
        conversationcreate = ConversationCreate.create(
            title="New Conversation",
            type=model_type,
            name=model_name,
            system_prompt=system_prompt
        )
        conversation = await self.conversation_service.create(conversationcreate)
        return conversation
        
    async def get_conversation_history(self, conversation_id: int, before_message_id: Optional[int] = None) -> List[MessageDTO]:
        try:
            messages = await self.message_service.list_by_conversation(conversation_id, before_message_id)
            return messages
        except NotFoundError:
            raise NotFoundError(f"Conversation {conversation_id} not found", source_class=self.__class__.__name__)
            
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

    def format_context(self, messages: List[MessageDTO], system_prompt: Optional[str] = None) -> str:
        """Format conversation history for LLM context"""
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append(f"System: {system_prompt}")
            
        # Add conversation history
        for msg in messages:
            role_prefix = "User: " if msg.role == "user" else "Assistant: "
            formatted_messages.append(f"{role_prefix}{msg.content}")
            
        return "\n".join(formatted_messages) 