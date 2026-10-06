from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    score: float = Field(..., description="Similarity score or reranked relevance score")
    raw_distance: Optional[float] = None


class RetrievalQueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=6, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(default=0.35, ge=0.0, le=1.0)
    enable_reranking: bool = True
    document_id_filter: Optional[str] = None


class RetrievalQueryResponse(BaseModel):
    query: str
    total_found: int
    chunks: List[RetrievedChunk]
    execution_time_ms: float


class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    quote: str
    relevance_score: float = 1.0


class GroundedAnswerSchema(BaseModel):
    answer: str
    confidence: Literal["high", "medium", "low", "unsupported"] = "high"
    is_grounded: bool = True
    insufficient_context: bool = False
    citations: List[Citation] = []
    unsupported_reasons: Optional[str] = None
