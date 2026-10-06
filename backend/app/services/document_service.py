import hashlib
import os
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.sql_models import DocumentModel, DocumentChunkModel
from app.ingestion.pdf_loader import DocumentExtractor, DocumentLoadError
from app.ingestion.chunker import RecursiveTextChunker
from app.llm.embeddings import embedding_service
from app.retrieval.vector_store import vector_store
from app.schemas.document import DocumentResponse, DocumentDetailResponse, IngestionConfig


class DocumentService:
    def __init__(self):
        Path(settings.UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
        Path(settings.SAMPLE_DOCS_DIRECTORY).mkdir(parents=True, exist_ok=True)

    def process_and_ingest(
        self,
        db: Session,
        file_path: str,
        filename: str,
        config: Optional[IngestionConfig] = None,
    ) -> DocumentModel:
        """
        Orchestrates full ingestion: File parse -> Chunking -> DB storage -> Embedding -> ChromaDB.
        """
        cfg = config or IngestionConfig(
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
        )

        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        # Create initial pending record
        doc_record = DocumentModel(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            status="processing",
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        try:
            # 1. Extract text and pages using PyMuPDF
            pages = DocumentExtractor.extract(file_path)
            doc_record.total_pages = len(pages)

            # 2. Chunk text preserving page attributions
            chunker = RecursiveTextChunker(
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap,
            )
            chunks = chunker.split_pages(pages)
            doc_record.chunk_count = len(chunks)

            # 3. Save chunks in SQLite
            chunk_models = [
                DocumentChunkModel(
                    document_id=doc_record.id,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    content=c.content,
                    token_estimate=c.token_estimate,
                )
                for c in chunks
            ]
            db.add_all(chunk_models)
            db.commit()

            # 4. Generate embeddings
            chunk_texts = [c.content for c in chunks]
            embeddings = embedding_service.embed_documents(chunk_texts)

            # 5. Store in ChromaDB vector store
            vector_store.add_chunks(
                chunks=chunks,
                document_id=doc_record.id,
                filename=doc_record.filename,
                embeddings=embeddings,
            )

            doc_record.status = "indexed"
            db.commit()
            db.refresh(doc_record)
            logger.info(
                f"Successfully ingested '{filename}' with {len(chunks)} chunks across {len(pages)} pages."
            )
            return doc_record

        except Exception as e:
            logger.error(f"Failed to ingest document '{filename}': {str(e)}", exc_info=True)
            doc_record.status = "error"
            doc_record.error_message = str(e)
            db.commit()
            db.refresh(doc_record)
            raise

    def list_documents(self, db: Session) -> List[DocumentModel]:
        return db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()

    def get_document(self, db: Session, document_id: str) -> Optional[DocumentModel]:
        return db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

    def delete_document(self, db: Session, document_id: str) -> bool:
        doc = self.get_document(db, document_id)
        if not doc:
            return False

        # 1. Remove from ChromaDB
        vector_store.delete_document_chunks(document_id)

        # 2. Remove physical file
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError as e:
                logger.warning(f"Could not remove file {doc.file_path}: {e}")

        # 3. Remove DB record (cascade deletes chunks)
        db.delete(doc)
        db.commit()
        logger.info(f"Deleted document {document_id} and its associated vector chunks.")
        return True


document_service = DocumentService()
