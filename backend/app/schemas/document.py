from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    page_number: int
    content: str
    token_estimate: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_size: int
    total_pages: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkRead] = []


class IngestionConfig(BaseModel):
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=150, ge=0, le=1000)


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
