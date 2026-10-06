import json
import re
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.llm.prompts import SYSTEM_PROMPT_RAG, QUERY_REFORMULATION_PROMPT
from app.schemas.retrieval import RetrievedChunk, GroundedAnswerSchema, Citation

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClient:
    """
    Coordinates LLM completions with structured Pydantic response parsing,
    strict grounding enforcement, and conversational query reformulation.
    """

    def __init__(self):
        self._client = None
        if settings.has_openai_key and OpenAI is not None:
            try:
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info(f"OpenAI LLM Client initialized with model: {settings.OPENAI_CHAT_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        else:
            logger.info("OpenAI API key not set or invalid. Running LLM in high-fidelity mock/deterministic mode.")

    @property
    def is_live_openai(self) -> bool:
        return self._client is not None

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        formatted_context: str,
    ) -> GroundedAnswerSchema:
        """
        Executes grounded generation against retrieved chunks with strict refusal when insufficient.
        """
        # 1. If no chunks passed the reranker/threshold, refuse immediately without hallucinating
        if not retrieved_chunks:
            logger.info("Zero context chunks retrieved above threshold. Generating grounded refusal.")
            return GroundedAnswerSchema(
                answer="Based on the provided documents, I do not have enough information to answer this question.",
                confidence="unsupported",
                is_grounded=False,
                insufficient_context=True,
                citations=[],
                unsupported_reasons="No relevant document sections matched your query above the relevance threshold.",
            )

        # 2. Live OpenAI Call
        if self._client:
            try:
                user_message = (
                    f"USER QUESTION: {query}\n\n"
                    f"RETRIEVED CONTEXT:\n{formatted_context}\n\n"
                    f"Please provide your grounded JSON response."
                )

                response = self._client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_RAG},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for deterministic factual extraction
                )

                content = response.choices[0].message.content
                data = json.loads(content)

                # Parse into Pydantic schema
                citations = [
                    Citation(
                        document_id=c.get("document_id", retrieved_chunks[0].document_id if retrieved_chunks else ""),
                        document_name=c.get("document_name", retrieved_chunks[0].filename if retrieved_chunks else "Document"),
                        page_number=int(c.get("page_number", 1)),
                        quote=c.get("quote", ""),
                        relevance_score=float(c.get("relevance_score", 1.0)),
                    )
                    for c in data.get("citations", [])
                ]

                # If LLM didn't attach citations but did provide an answer grounded in chunks, backfill top chunks
                if not citations and not data.get("insufficient_context", False):
                    for c in retrieved_chunks[:2]:
                        citations.append(
                            Citation(
                                document_id=c.document_id,
                                document_name=c.filename,
                                page_number=c.page_number,
                                quote=c.content[:160] + "...",
                                relevance_score=c.score,
                            )
                        )

                return GroundedAnswerSchema(
                    answer=data.get("answer", "No answer generated."),
                    confidence=data.get("confidence", "high"),
                    is_grounded=data.get("is_grounded", True),
                    insufficient_context=data.get("insufficient_context", False),
                    citations=citations,
                    unsupported_reasons=data.get("unsupported_reasons"),
                )
            except Exception as e:
                logger.error(f"OpenAI completion failed: {e}. Falling back to internal grounded answer generator.")
                return self._generate_fallback_answer(query, retrieved_chunks)

        # 3. High-fidelity fallback synthesizer (for local testing without API key)
        return self._generate_fallback_answer(query, retrieved_chunks)

    def reformulate_query(self, user_query: str, chat_history_str: str) -> str:
        """
        Reformulates conversational follow-up questions into standalone search queries.
        """
        if not chat_history_str.strip():
            return user_query

        if self._client:
            try:
                prompt = QUERY_REFORMULATION_PROMPT.format(
                    chat_history=chat_history_str,
                    user_query=user_query,
                )
                response = self._client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=60,
                )
                rewritten = response.choices[0].message.content.strip().strip('"')
                if rewritten:
                    logger.info(f"Query reformulated: '{user_query}' -> '{rewritten}'")
                    return rewritten
            except Exception as e:
                logger.warning(f"Query reformulation failed: {e}. Using raw query.")

        # Fallback heuristic: If question contains demonstrative pronouns, combine with latest keywords
        ambiguous_words = {"it", "this", "that", "they", "those", "the policy", "the limit", "the guideline"}
        words = set(user_query.lower().split())
        if words.intersection(ambiguous_words):
            # Extract last user topic if available
            lines = [l for l in chat_history_str.splitlines() if l.startswith("User:")]
            if lines:
                last_question = lines[-1].replace("User:", "").strip()
                return f"{user_query} ({last_question})"

        return user_query

    def _generate_fallback_answer(
        self, query: str, retrieved_chunks: List[RetrievedChunk]
    ) -> GroundedAnswerSchema:
        """
        Synthesizes a strictly grounded response directly from the top chunks.
        Used for offline mode or when OpenAI keys are unavailable.
        """
        top_chunk = retrieved_chunks[0]

        stopwords = {
            "a", "an", "the", "in", "on", "of", "to", "for", "with", "at", "by", "from",
            "is", "are", "was", "were", "what", "how", "why", "when", "where", "who",
            "which", "does", "do", "did", "can", "could", "should", "would", "about",
            "it", "this", "that", "and", "or", "but", "be", "been", "being", "tell", "me",
        }
        query_words = {w for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query.lower()) if w not in stopwords}
        selected_sentences = []

        for chunk in retrieved_chunks[:3]:
            sentences = chunk.content.split(". ")
            for s in sentences:
                s_words = {w for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", s.lower()) if w not in stopwords}
                if len(query_words.intersection(s_words)) >= 2:
                    clean_s = s.strip()
                    if clean_s and not clean_s.endswith("."):
                        clean_s += "."
                    if clean_s not in selected_sentences:
                        selected_sentences.append(clean_s)

        if not selected_sentences:
            return GroundedAnswerSchema(
                answer="Based on the provided documents, I do not have enough information to answer this question.",
                confidence="unsupported",
                is_grounded=False,
                insufficient_context=True,
                citations=[],
                unsupported_reasons="The retrieved document sections do not contain information related to your question.",
            )

        synthesized_text = (
            f"According to **{top_chunk.filename}** (Page {top_chunk.page_number}):\n\n"
            + " ".join(selected_sentences[:4])
            + f" [Doc: {top_chunk.filename}, Page: {top_chunk.page_number}]"
        )

        citations = [
            Citation(
                document_id=c.document_id,
                document_name=c.filename,
                page_number=c.page_number,
                quote=c.content[:160] + "...",
                relevance_score=c.score,
            )
            for c in retrieved_chunks[:min(3, len(retrieved_chunks))]
        ]

        return GroundedAnswerSchema(
            answer=synthesized_text,
            confidence="high" if top_chunk.score > 0.6 else "medium",
            is_grounded=True,
            insufficient_context=False,
            citations=citations,
            unsupported_reasons=None,
        )


llm_client = LLMClient()
