import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=True)
    total_pages = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, indexed, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("DocumentChunkModel", back_populates="document", cascade="all, delete-orphan")


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_estimate = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="chunks")


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan", order_by="MessageModel.created_at")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)  # JSON serialized list of Citation dicts
    is_grounded = Column(Boolean, default=True)
    confidence = Column(String(20), default="high")  # high, medium, low, unsupported
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ConversationModel", back_populates="messages")


class EvaluationRecordModel(Base):
    __tablename__ = "evaluation_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question = Column(Text, nullable=False)
    expected_doc = Column(String(255), nullable=True)
    retrieved_docs_json = Column(Text, nullable=True)
    answer = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    grounding_score = Column(Float, default=0.0)
    citation_present = Column(Boolean, default=False)
    is_hallucination_refusal = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)
    status = Column(String(20), default="passed")  # passed, failed, review
    created_at = Column(DateTime, default=datetime.utcnow)
