from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.core.logging import logger
from app.ingestion.chunker import Chunk
from app.schemas.retrieval import RetrievedChunk


class VectorStoreManager:
    """
    Manages persistent vector storage using ChromaDB.
    Uses Cosine distance metric for semantic chunk matching.
    """

    def __init__(self):
        Path(settings.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB initialized. Collection: '{settings.CHROMA_COLLECTION_NAME}', "
            f"Current vectors: {self.collection.count()}"
        )

    def count(self) -> int:
        return self.collection.count()

    def add_chunks(
        self,
        chunks: List[Chunk],
        document_id: str,
        filename: str,
        embeddings: List[List[float]],
    ) -> int:
        if not chunks:
            return 0

        ids = [f"{document_id}_chunk_{c.chunk_index}" for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "page_number": int(c.page_number),
                "chunk_index": int(c.chunk_index),
                "token_estimate": int(c.token_estimate),
            }
            for c in chunks
        ]

        # ChromaDB allows batch upserts
        batch_size = 200
        for i in range(0, len(ids), batch_size):
            end_idx = i + batch_size
            self.collection.upsert(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
            )

        logger.info(f"Upserted {len(chunks)} chunks into ChromaDB for doc '{filename}' (ID: {document_id})")
        return len(chunks)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 6,
        document_id: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        if self.collection.count() == 0:
            return []

        where_filter = {"document_id": document_id} if document_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[RetrievedChunk] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

        for chunk_id, content, meta, dist in zip(ids, docs, metas, distances):
            # For cosine distance: distance is 1 - similarity.
            # Convert to similarity score between 0.0 and 1.0
            similarity_score = max(0.0, min(1.0, 1.0 - (dist if dist is not None else 0.0)))
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", "unknown"),
                    page_number=int(meta.get("page_number", 1)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    content=content,
                    score=round(similarity_score, 4),
                    raw_distance=dist,
                )
            )

        return retrieved

    def delete_document_chunks(self, document_id: str) -> int:
        before_count = self.collection.count()
        self.collection.delete(where={"document_id": document_id})
        after_count = self.collection.count()
        deleted = before_count - after_count
        logger.info(f"Deleted {deleted} chunks for doc {document_id} from ChromaDB")
        return deleted


vector_store = VectorStoreManager()
