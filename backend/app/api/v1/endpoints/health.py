from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.retrieval.vector_store import vector_store

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Test DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Test ChromaDB
    chroma_ok = False
    vector_count = 0
    try:
        vector_count = vector_store.count()
        chroma_ok = True
    except Exception:
        chroma_ok = False

    return {
        "status": "healthy" if db_ok and chroma_ok else "degraded",
        "version": settings.PROJECT_VERSION,
        "database": {"connected": db_ok, "type": "sqlite"},
        "vector_store": {
            "connected": chroma_ok,
            "type": "chromadb",
            "collection": settings.CHROMA_COLLECTION_NAME,
            "total_vectors": vector_count,
        },
        "openai": {
            "configured": settings.has_openai_key,
            "chat_model": settings.OPENAI_CHAT_MODEL,
            "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
            "mode": "live_api" if settings.has_openai_key else "offline_deterministic_fallback",
        },
    }
