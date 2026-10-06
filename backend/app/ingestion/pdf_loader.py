import os
from pathlib import Path
from typing import List, Dict, Any
import pymupdf
from app.core.logging import logger


class DocumentLoadError(Exception):
    pass


class ExtractedPage:
    def __init__(self, page_number: int, text: str, word_count: int):
        self.page_number = page_number
        self.text = text
        self.word_count = word_count


class DocumentExtractor:
    """
    Extracts text and page-level metadata from documents (PDF, TXT, MD).
    Uses PyMuPDF (fitz) for PDF files for high-speed, accurate text parsing.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    @classmethod
    def extract(cls, file_path: str) -> List[ExtractedPage]:
        path = Path(file_path)
        if not path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise DocumentLoadError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

        if ext == ".pdf":
            return cls._extract_pdf(str(path))
        else:
            return cls._extract_text(str(path))

    @classmethod
    def _extract_pdf(cls, file_path: str) -> List[ExtractedPage]:
        pages: List[ExtractedPage] = []
        try:
            doc = pymupdf.open(file_path)
            total_pages = len(doc)
            logger.info(f"Extracting PDF: {file_path} ({total_pages} pages)")

            for page_idx in range(total_pages):
                page = doc[page_idx]
                text = page.get_text("text") or ""
                # Clean whitespace but preserve paragraph structure
                cleaned_text = "\n".join(
                    line.strip() for line in text.splitlines() if line.strip()
                )
                word_count = len(cleaned_text.split())
                pages.append(
                    ExtractedPage(
                        page_number=page_idx + 1,  # 1-indexed for humans
                        text=cleaned_text,
                        word_count=word_count,
                    )
                )

            doc.close()
            # Validate that at least some text was extracted
            total_text_length = sum(len(p.text) for p in pages)
            if total_text_length == 0:
                raise DocumentLoadError(
                    "The PDF contains no extractable text. It may be a scanned image or empty document."
                )

            return pages
        except Exception as e:
            if isinstance(e, DocumentLoadError):
                raise
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            raise DocumentLoadError(f"Failed to parse PDF document: {str(e)}") from e

    @classmethod
    def _extract_text(cls, file_path: str) -> List[ExtractedPage]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if not content.strip():
                raise DocumentLoadError("Text document is empty.")

            cleaned_text = content.strip()
            return [
                ExtractedPage(
                    page_number=1,
                    text=cleaned_text,
                    word_count=len(cleaned_text.split()),
                )
            ]
        except Exception as e:
            if isinstance(e, DocumentLoadError):
                raise
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            raise DocumentLoadError(f"Failed to read text file: {str(e)}") from e
