from fastapi import APIRouter, Depends
from opentelemetry import trace
from websrc.config.logging_manager import LoggingManager
from src.dependencies.container import ConversationServiceDependency, MessageServiceDependency
from src.models.pydantic import ConversationCreate, MessageCreate, ConversationUpdate
from exceptions.exceptions import NotFoundError

router = APIRouter()
logging_manager = LoggingManager()

@router.post("/conversations/")
@logging_manager.log_and_trace("create_conversation")
async def create_conversation(
    conversation: ConversationCreate,
    conversation_service: ConversationServiceDependency,
    message_service: MessageServiceDependency
):
    conversation = await conversation_service.create(data=conversation)
    
    # Add default welcome message
    welcome_message = MessageCreate(
        role="assistant",
        content="Welcome! I'm your AI assistant. How can I help you today?"
    )
    await message_service.create(
        conversation_id=conversation.id,
        data=welcome_message
    )
    
    return {"id": conversation.id}

@router.get("/conversations/{conversation_id}")
@logging_manager.log_and_trace("get_conversation")
async def get_conversation(
    conversation_id: int,
    conversation_service: ConversationServiceDependency
):
    conversation = await conversation_service.get(conversation_id)
    return conversation



@router.post("/conversations/{conversation_id}/messages")
@logging_manager.log_and_trace("add_message")
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    conversation_service: ConversationServiceDependency,
    message_service: MessageServiceDependency
):
    # Verify conversation exists
    conversation = await conversation_service.get(conversation_id)
    if not conversation:
        raise NotFoundError(f"Conversation {conversation_id} not found")
        
    message = await message_service.create(
        conversation_id=conversation_id,
        data=message
    )
    return {"id": message.id}

@router.get("/conversations/")
@logging_manager.log_and_trace("list_conversations")
async def list_conversations(
    conversation_service: ConversationServiceDependency
):
    conversations = await conversation_service.list()
    return conversations

@router.get("/conversations/{conversation_id}/messages")
@logging_manager.log_and_trace("get_conversation_messages")
async def get_conversation_messages(
    conversation_id: int,
    conversation_service: ConversationServiceDependency,
    message_service: MessageServiceDependency
):
    conversation = await conversation_service.get(conversation_id)
    if not conversation:
        raise NotFoundError(
            f"Conversation {conversation_id} not found",
            details={"conversation_id": conversation_id}
        )
        
    messages = await message_service.list_by_conversation(conversation_id)
    return {"messages": messages}

@router.patch("/conversations/{conversation_id}")
@logging_manager.log_and_trace("update_conversation")
async def update_conversation(
    conversation_id: int,
    conversation: ConversationUpdate,
    conversation_service: ConversationServiceDependency
):
    updated = await conversation_service.update(
        id=conversation_id,
        data=conversation
    )
    if not updated:
        raise NotFoundError(
            f"Conversation {conversation_id} not found",
            details={"conversation_id": conversation_id}
        )
    return updated

@router.delete("/conversations/{conversation_id}")
@logging_manager.log_and_trace("delete_conversation")
async def delete_conversation(
    conversation_id: int,
    conversation_service: ConversationServiceDependency
):
    await conversation_service.delete(conversation_id)
    return {"message": "Conversation deleted successfully"} 