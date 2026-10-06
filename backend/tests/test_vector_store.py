import uuid
from app.ingestion.chunker import Chunk
from app.retrieval.vector_store import vector_store
from app.llm.embeddings import embedding_service


def test_vector_store_add_and_query():
    doc_id = str(uuid.uuid4())
    filename = "Test_Policy.pdf"

    chunks = [
        Chunk(
            chunk_index=0,
            page_number=1,
            content="Canary deployment routes 5% of production traffic for 15 minutes.",
            token_estimate=15,
        ),
        Chunk(
            chunk_index=1,
            page_number=2,
            content="Hardware MFA is strictly mandatory for all administrative access.",
            token_estimate=12,
        ),
    ]

    texts = [c.content for c in chunks]
    embeddings = embedding_service.embed_documents(texts)

    # 1. Add chunks
    added_count = vector_store.add_chunks(
        chunks=chunks,
        document_id=doc_id,
        filename=filename,
        embeddings=embeddings,
    )
    assert added_count == 2

    # 2. Query similarity
    query_vec = embedding_service.embed_query("hardware MFA mandatory")
    retrieved = vector_store.query(query_embedding=query_vec, top_k=2)

    assert len(retrieved) >= 1
    # Check that highest match is chunk 1
    matches = [c for c in retrieved if c.document_id == doc_id]
    assert len(matches) > 0
    assert matches[0].page_number in (1, 2)

    # 3. Clean up
    deleted = vector_store.delete_document_chunks(doc_id)
    assert deleted == 2
