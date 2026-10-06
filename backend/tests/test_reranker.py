from app.schemas.retrieval import RetrievedChunk
from app.retrieval.reranker import RerankerFilter


def test_reranker_threshold_filtering():
    filter_engine = RerankerFilter(similarity_threshold=0.4)

    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            filename="DocA.pdf",
            page_number=1,
            chunk_index=0,
            content="Canary deployment error rate threshold is 0.2 percent.",
            score=0.8,
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="d2",
            filename="DocB.pdf",
            page_number=1,
            chunk_index=0,
            content="Unrelated weather forecasting and cloud computing.",
            score=0.25,  # Below 0.4 threshold
        ),
    ]

    filtered = filter_engine.rerank_and_filter("canary error rate", chunks, top_k=2)

    assert len(filtered) == 1
    assert filtered[0].chunk_id == "c1"
    assert filtered[0].score > 0.5


def test_reranker_lexical_boost():
    filter_engine = RerankerFilter(similarity_threshold=0.3)

    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            filename="DocA.pdf",
            page_number=1,
            chunk_index=0,
            content="The standard password rotation policy requires 90 days interval.",
            score=0.6,
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="d2",
            filename="DocB.pdf",
            page_number=1,
            chunk_index=0,
            content="All employees have access to gym facilities on weekends.",
            score=0.6,
        ),
    ]

    reranked = filter_engine.rerank_and_filter("password rotation policy 90 days", chunks, top_k=2)
    assert len(reranked) == 2
    # c1 should be scored significantly higher due to lexical overlap
    assert reranked[0].chunk_id == "c1"
    assert reranked[0].score > reranked[1].score
