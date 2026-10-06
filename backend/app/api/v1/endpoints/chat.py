from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.chat_service import chat_service
from app.schemas.chat import (
    ChatMessageRequest,
    ChatResponse,
    ConversationResponse,
    ConversationDetailResponse,
)

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
def send_chat_message(request: ChatMessageRequest, db: Session = Depends(get_db)):
    try:
        response = chat_service.process_chat_message(db, request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}",
        )


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return chat_service.list_conversations(db)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = chat_service.get_conversation_detail(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found.",
        )
    return conv


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    success = chat_service.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found.",
        )
    return {"message": "Conversation successfully deleted.", "conversation_id": conversation_id}
