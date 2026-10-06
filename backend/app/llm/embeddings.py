import hashlib
import math
import numpy as np
from typing import List
from app.core.config import settings
from app.core.logging import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class EmbeddingService:
    """
    Manages embedding generation for documents and queries.
    Uses OpenAI's text-embedding-3-small (1536-dim).
    Falls back to a deterministic normalized semantic representation when
    no OpenAI API key is configured, allowing offline development and testing.
    """

    DIMENSION = 1536

    def __init__(self):
        self._client = None
        if settings.has_openai_key and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI Embedding client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}. Fallback enabled.")
        else:
            logger.info("No OpenAI API key detected. Running embeddings in local deterministic fallback mode.")

    @property
    def is_live_openai(self) -> bool:
        return self._client is not None

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """
        Embeds a list of document chunk texts.
        """
        if not texts:
            return []

        if self._client:
            try:
                all_embeddings: List[List[float]] = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    # OpenAI recommends replacing newlines with spaces
                    cleaned_batch = [t.replace("\n", " ") for t in batch]
                    response = self._client.embeddings.create(
                        model=settings.OPENAI_EMBEDDING_MODEL,
                        input=cleaned_batch,
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                return all_embeddings
            except Exception as e:
                logger.warning(f"OpenAI embedding call failed ({str(e)}). Falling back to local vectors.")
                return [self._generate_fallback_vector(t) for t in texts]

        return [self._generate_fallback_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a single search query.
        """
        results = self.embed_documents([query])
        return results[0]

    def _generate_fallback_vector(self, text: str) -> List[float]:
        """
        Generates a deterministic 1536-dimensional normalized vector for offline mode.
        Uses bag-of-words character n-grams and hashing to yield meaningful relative cosine similarity.
        """
        vec = np.zeros(self.DIMENSION, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            # Hash tokens to indices
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIMENSION
            weight = 1.0 + (len(word) / 10.0)
            vec[idx] += weight

        # Also add bigram hash
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIMENSION
            vec[idx] += 1.5

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()


embedding_service = EmbeddingService()
