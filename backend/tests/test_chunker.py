import pytest
from app.ingestion.pdf_loader import ExtractedPage
from app.ingestion.chunker import RecursiveTextChunker


def test_chunker_preserves_page_numbers():
    pages = [
        ExtractedPage(page_number=1, text="Page one first paragraph.\n\nPage one second paragraph.", word_count=8),
        ExtractedPage(page_number=2, text="Page two starts here with important security rules.", word_count=8),
    ]

    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split_pages(pages)

    assert len(chunks) >= 2
    # Verify page attribution
    page_1_chunks = [c for c in chunks if c.page_number == 1]
    page_2_chunks = [c for c in chunks if c.page_number == 2]

    assert len(page_1_chunks) > 0
    assert len(page_2_chunks) > 0
    assert "Page two" in page_2_chunks[0].content


def test_chunker_handles_large_text_within_bounds():
    long_text = "Enterprise knowledge management ensures high retrieval precision. " * 30
    pages = [ExtractedPage(page_number=1, text=long_text, word_count=len(long_text.split()))]

    chunker = RecursiveTextChunker(chunk_size=200, chunk_overlap=50)
    chunks = chunker.split_pages(pages)

    assert len(chunks) > 1
    for chunk in chunks:
        # Check that individual chunks are not excessively large
        assert len(chunk.content) <= 300
        assert chunk.token_estimate > 0


def test_chunker_invalid_overlap_raises():
    with pytest.raises(ValueError):
        RecursiveTextChunker(chunk_size=100, chunk_overlap=150)
