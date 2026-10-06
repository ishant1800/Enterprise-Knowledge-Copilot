import time
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.llm.embeddings import embedding_service
from app.retrieval.vector_store import vector_store
from app.retrieval.reranker import reranker
from app.schemas.retrieval import RetrievedChunk, RetrievalQueryResponse


class RetrieverService:
    """
    Coordinates semantic vector retrieval and reranking for the RAG pipeline.
    """

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: Optional[float] = None,
        enable_reranking: bool = True,
        document_id_filter: Optional[str] = None,
    ) -> Tuple[List[RetrievedChunk], float]:
        start_time = time.time()
        k = top_k or settings.TOP_K_RETRIEVAL

        logger.info(f"Retrieving context for query: '{query}' (top_k={k})")

        # 1. Embed query
        query_embedding = embedding_service.embed_query(query)

        # 2. Vector search (fetch 2x candidates if reranking is enabled)
        candidate_count = k * 2 if enable_reranking else k
        raw_candidates = vector_store.query(
            query_embedding=query_embedding,
            top_k=candidate_count,
            document_id=document_id_filter,
        )

        if not raw_candidates:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return [], round(elapsed_ms, 2)

        # 3. Rerank and filter candidates
        if enable_reranking and settings.ENABLE_RERANKING:
            custom_reranker = reranker
            if similarity_threshold is not None:
                from app.retrieval.reranker import RerankerFilter
                custom_reranker = RerankerFilter(similarity_threshold=similarity_threshold)
            final_chunks = custom_reranker.rerank_and_filter(
                query=query,
                chunks=raw_candidates,
                top_k=k,
            )
        else:
            thresh = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
            final_chunks = [c for c in raw_candidates if c.score >= thresh][:k]

        elapsed_ms = (time.time() - start_time) * 1000.0
        return final_chunks, round(elapsed_ms, 2)

    def format_context_for_prompt(self, chunks: List[RetrievedChunk]) -> str:
        """
        Formats retrieved chunks into structured context blocks with clear provenance metadata.
        """
        if not chunks:
            return "NO RETRIEVED CONTEXT AVAILABLE."

        formatted_blocks = []
        for i, chunk in enumerate(chunks, 1):
            block = (
                f"--- SOURCE CHUNK [{i}] ---\n"
                f"Document: {chunk.filename}\n"
                f"Page: {chunk.page_number}\n"
                f"Relevance Score: {chunk.score:.2f}\n"
                f"Excerpt:\n{chunk.content}\n"
            )
            formatted_blocks.append(block)

        return "\n".join(formatted_blocks)


retriever_service = RetrieverService()
