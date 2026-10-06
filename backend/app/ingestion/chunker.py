import re
from typing import List, Dict, Any, Optional
from app.ingestion.pdf_loader import ExtractedPage
from app.core.logging import logger


class Chunk:
    def __init__(
        self,
        chunk_index: int,
        page_number: int,
        content: str,
        token_estimate: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.token_estimate = token_estimate
        self.metadata = metadata or {}


class RecursiveTextChunker:
    """
    Splits text recursively based on natural semantic boundaries:
    paragraphs (\n\n) -> sentences (\n, . ) -> words -> characters,
    while maintaining overlap to prevent information fragmentation across boundaries.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_pages(self, pages: List[ExtractedPage]) -> List[Chunk]:
        """
        Splits extracted pages into chunks, preserving page attribution for every chunk.
        """
        chunks: List[Chunk] = []
        global_chunk_index = 0

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self._chunk_text(page_text)
            for text_segment in page_chunks:
                # Approximate token count (1 token ~= 4 characters in English)
                token_estimate = max(1, len(text_segment) // 4)
                chunks.append(
                    Chunk(
                        chunk_index=global_chunk_index,
                        page_number=page.page_number,
                        content=text_segment,
                        token_estimate=token_estimate,
                        metadata={
                            "page_number": page.page_number,
                            "chunk_index": global_chunk_index,
                        },
                    )
                )
                global_chunk_index += 1

        logger.info(
            f"Chunked {len(pages)} pages into {len(chunks)} chunks "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        # Split into logical sections by paragraphs first
        paragraphs = re.split(r"\n\s*\n", text)
        result: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If a single paragraph is larger than chunk_size, split by sentences
            if len(para) > self.chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            result.append(current_chunk)
                            # Overlap from tail of previous chunk
                            overlap_text = current_chunk[-self.chunk_overlap :]
                            current_chunk = f"{overlap_text} {sentence}".strip()
                        else:
                            # Sentence itself exceeds chunk size, hard split by character window
                            for i in range(0, len(sentence), self.chunk_size - self.chunk_overlap):
                                seg = sentence[i : i + self.chunk_size].strip()
                                if seg:
                                    result.append(seg)
                            current_chunk = ""
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk = f"{current_chunk}\n\n{para}"
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        result.append(current_chunk)
                        overlap_text = current_chunk[-self.chunk_overlap :]
                        current_chunk = f"{overlap_text}\n\n{para}".strip()
                    else:
                        result.append(para)
                        current_chunk = ""

        if current_chunk and current_chunk not in result:
            result.append(current_chunk)

        # Filter out empty or tiny residual chunks
        return [c for c in result if len(c.strip()) > 20]
