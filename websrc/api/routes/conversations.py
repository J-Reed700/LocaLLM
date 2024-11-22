from fastapi import APIRouter, Depends, HTTPException
from src.services.database import DatabaseService
from src.services.container import container
from src.models.pydantic import ConversationCreate, MessageCreate, ConversationUpdate
from src.models.database import MessageRoleEnum
from typing import List
from websrc.config.logging_config import log_async_function

router = APIRouter()

@router.post("/conversations/")
@log_async_function
async def create_conversation(
    conversation: ConversationCreate,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        # Create a new conversation with the specified model configuration
        conversation = await db.create_conversation(
            title=conversation.title,
            model_type=conversation.model_type,
            model_name=conversation.model_name
        )
        return {"id": conversation.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages")
@log_async_function
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        # Add message to conversation
        message = await db.add_message(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            generation_info=message.metadata  # Updated to match the new column name
        )
        return {"id": message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/")
@log_async_function
async def list_conversations(
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        conversations = await db.list_conversations()
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
@log_async_function
async def get_conversation_messages(
    conversation_id: int,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        messages = await db.get_conversation_messages(conversation_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/conversations/{conversation_id}")
@log_async_function
async def update_conversation(
    conversation_id: int,
    conversation: ConversationUpdate,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        updated = await db.update_conversation(
            conversation_id=conversation_id,
            title=conversation.title
        )
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))