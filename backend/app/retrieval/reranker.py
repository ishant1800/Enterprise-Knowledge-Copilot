import re
from typing import List
from app.schemas.retrieval import RetrievedChunk
from app.core.config import settings
from app.core.logging import logger


class RerankerFilter:
    """
    Reranks and filters retrieved chunks:
    1. Hybrid Lexical-Semantic Re-scoring: Combines dense vector similarity with BM25-style keyword coverage.
    2. Dynamic Relevance Threshold: Filters out irrelevant noise chunks.
    3. Redundancy reduction: Avoids repeating near-identical text from adjacent overlapping chunks.
    """

    def __init__(self, similarity_threshold: float = None):
        self.threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SIMILARITY_THRESHOLD
        )

    def rerank_and_filter(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        if not chunks:
            return []

        query_terms = self._extract_terms(query)
        logger.debug(f"Reranking {len(chunks)} chunks for query terms: {query_terms}")

        scored_candidates: List[RetrievedChunk] = []

        for chunk in chunks:
            # 1. Compute lexical coverage score (BM25-style keyword match ratio)
            lexical_score = self._compute_lexical_overlap(query_terms, chunk.content)

            # 2. Hybrid score: 60% semantic similarity + 40% lexical keyword overlap
            hybrid_score = (0.6 * chunk.score) + (0.4 * lexical_score)

            # 3. Relevance threshold check:
            # Candidate passes only if hybrid score meets threshold OR significant lexical overlap exists
            if hybrid_score < self.threshold and lexical_score < 0.25:
                logger.debug(
                    f"Discarded chunk {chunk.chunk_id}: hybrid={hybrid_score:.3f} < threshold {self.threshold}"
                )
                continue

            chunk.score = round(hybrid_score, 4)
            scored_candidates.append(chunk)

        # Sort descending by hybrid score
        scored_candidates.sort(key=lambda c: c.score, reverse=True)

        # 4. Redundancy filter: Deduplicate chunks that share > 80% identical text
        filtered_results: List[RetrievedChunk] = []
        for candidate in scored_candidates:
            if not self._is_redundant(candidate, filtered_results):
                filtered_results.append(candidate)
            if len(filtered_results) >= top_k:
                break

        logger.info(
            f"Reranker: {len(chunks)} initial -> {len(scored_candidates)} above threshold -> "
            f"{len(filtered_results)} final selected."
        )
        return filtered_results

    def _extract_terms(self, text: str) -> set:
        stopwords = {
            "a", "an", "the", "in", "on", "of", "to", "for", "with", "at", "by", "from",
            "is", "are", "was", "were", "what", "how", "why", "when", "where", "who",
            "does", "do", "did", "can", "could", "should", "would", "about", "it", "this",
            "that", "and", "or", "but", "be", "been", "being",
        }
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
        return {t for t in tokens if t not in stopwords}

    def _compute_lexical_overlap(self, query_terms: set, content: str) -> float:
        if not query_terms:
            return 0.5
        content_lower = content.lower()
        matched = sum(1 for term in query_terms if term in content_lower)
        return min(1.0, matched / len(query_terms))

    def _is_redundant(self, candidate: RetrievedChunk, existing: List[RetrievedChunk]) -> bool:
        candidate_words = set(candidate.content.lower().split()[:30])
        for ex in existing:
            if ex.document_id == candidate.document_id:
                ex_words = set(ex.content.lower().split()[:30])
                overlap = len(candidate_words.intersection(ex_words))
                if overlap > 20:  # Highly overlapping adjacent chunk
                    return True
        return False


reranker = RerankerFilter()
