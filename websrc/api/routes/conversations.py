from fastapi import APIRouter, Depends, HTTPException
from src.services.database import DatabaseService
from src.services.container import container
from websrc.models.pydantic import ConversationCreate, MessageCreate
from typing import List

router = APIRouter()

@router.post("/conversations/")
async def create_conversation(
    conversation: ConversationCreate,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        # Hardcoded user_id for now - implement proper auth later
        user_id = 1
        conversation = await db.create_conversation(
            user_id=user_id,
            title=conversation.title,
            model_type=conversation.model_type,
            model_name=conversation.model_name
        )
        return {"id": conversation.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    db: DatabaseService = Depends(lambda: container.db_service)
):
    try:
        message = await db.add_message(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            metadata=message.metadata
        )
        return {"id": message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 