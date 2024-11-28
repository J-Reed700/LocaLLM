from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from src.services.conversation_service import ConversationService
from src.services.container import get_conversation_service_dependency, get_message_service_dependency
from src.models.pydantic import ConversationCreate, MessageCreate, ConversationUpdate
from src.models.database import MessageRoleEnum
from typing import List
from websrc.config.logging_config import log_endpoint, track_span_exceptions
from websrc.api.exceptions.exceptions import (
    DatabaseError, 
    NotFoundError, 
    ValidationError, 
    DatabaseConnectionError
)
from src.services.message_service import MessageService

router = APIRouter()

@router.post("/conversations/")
@log_endpoint
@track_span_exceptions()
async def create_conversation(
    conversation: ConversationCreate,
    conversation_service: ConversationService = Depends(get_conversation_service_dependency)
):
    conversation = await conversation_service.create(data=conversation)
    return {"id": conversation.id}

@router.post("/conversations/{conversation_id}/messages")
@log_endpoint
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    conversation_service: ConversationService = Depends(get_conversation_service_dependency),
    message_service: MessageService = Depends(get_message_service_dependency)
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
@log_endpoint
@track_span_exceptions()
async def list_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service_dependency)
):
    conversations = await conversation_service.list()
    return conversations

@router.get("/conversations/{conversation_id}/messages")
@log_endpoint       
@track_span_exceptions()
async def get_conversation_messages(
    conversation_id: int,
    conversation_service: ConversationService = Depends(get_conversation_service_dependency),
    message_service: MessageService = Depends(get_message_service_dependency)
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
@log_endpoint
@track_span_exceptions()
async def update_conversation(
    conversation_id: int,
    conversation: ConversationUpdate,
    conversation_service: ConversationService = Depends(get_conversation_service_dependency)
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
