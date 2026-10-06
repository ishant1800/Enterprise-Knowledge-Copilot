import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.database import get_db
from app.services.document_service import document_service
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUploadResponse,
    IngestionConfig,
)

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(800),
    chunk_overlap: Optional[int] = Form(150),
    db: Session = Depends(get_db),
):
    # 1. Validate filename & extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".txt", ".md"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Please upload .pdf, .txt, or .md documents.",
        )

    # 2. Check max file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 3. Save uploaded file to disk
    save_path = Path(settings.UPLOAD_DIRECTORY) / file.filename
    # Avoid overwriting directly if duplicate name
    counter = 1
    stem = save_path.stem
    while save_path.exists():
        save_path = Path(settings.UPLOAD_DIRECTORY) / f"{stem}_{counter}{ext}"
        counter += 1

    with open(save_path, "wb") as f:
        f.write(content)

    # 4. Ingest and index
    cfg = IngestionConfig(
        chunk_size=chunk_size or settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP,
    )

    try:
        doc = document_service.process_and_ingest(
            db=db,
            file_path=str(save_path),
            filename=save_path.name,
            config=cfg,
        )
        return DocumentUploadResponse(
            document_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            message=f"Document successfully ingested into {doc.chunk_count} chunks across {doc.total_pages} pages.",
        )
    except Exception as e:
        logger.error(f"Ingestion failed for {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion error: {str(e)}",
        )


@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    docs = document_service.list_documents(db)
    return docs


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = document_service.get_document(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    success = document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )
    return {"message": "Document and associated vectors successfully deleted.", "document_id": document_id}


@router.post("/seed-samples")
def seed_sample_documents(db: Session = Depends(get_db)):
    """
    Ingests pre-generated sample documents if present in the sample_docs directory.
    """
    sample_dir = Path(settings.SAMPLE_DOCS_DIRECTORY)
    if not sample_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample documents directory not found.",
        )

    from app.models.sql_models import DocumentModel
    from app.retrieval.vector_store import vector_store

    ingested = []
    for file_path in sample_dir.glob("*.pdf"):
        exists = db.query(DocumentModel).filter(DocumentModel.filename == file_path.name).first()
        dest = Path(settings.UPLOAD_DIRECTORY) / file_path.name

        if exists and vector_store.count() > 0 and exists.status == "indexed":
            ingested.append({"filename": exists.filename, "chunks": exists.chunk_count})
            continue

        try:
            if exists:
                document_service.delete_document(db, exists.id)

            shutil.copy2(file_path, dest)
            doc = document_service.process_and_ingest(
                db=db,
                file_path=str(dest),
                filename=dest.name,
            )
            ingested.append({"filename": doc.filename, "chunks": doc.chunk_count})
        except Exception as e:
            logger.error(f"Failed to seed {file_path.name}: {e}")

    return {
        "message": f"Successfully seeded {len(ingested)} sample documents.",
        "documents": ingested,
    }
