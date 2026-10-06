from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.retrieval import Citation, RetrievedChunk


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=15)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    enable_reranking: bool = True
    document_id_filter: Optional[str] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Citation] = []
    is_grounded: bool = True
    confidence: Literal["high", "medium", "low", "unsupported"] = "high"
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    retrieved_chunks: List[RetrievedChunk] = []
    rewritten_query: Optional[str] = None
    execution_time_ms: float


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
