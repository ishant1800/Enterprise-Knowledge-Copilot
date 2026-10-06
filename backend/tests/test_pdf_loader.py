import pytest
from pathlib import Path
from app.ingestion.pdf_loader import DocumentExtractor, DocumentLoadError


def test_pdf_extraction_real_file():
    pdf_path = Path(__file__).resolve().parent.parent / "data" / "sample_docs" / "Enterprise_AI_Security_Policy.pdf"
    assert pdf_path.exists(), "Sample PDF must exist for testing"

    pages = DocumentExtractor.extract(str(pdf_path))
    assert len(pages) == 3
    assert pages[0].page_number == 1
    assert "Data Classification" in pages[0].text
    assert "Password Rotation" in pages[1].text
    assert pages[0].word_count > 10


def test_unsupported_file_extension():
    with pytest.raises(DocumentLoadError):
        DocumentExtractor.extract("invalid_file.xyz")
