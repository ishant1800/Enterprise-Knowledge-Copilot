from fastapi import APIRouter
from app.retrieval.retriever import retriever_service
from app.schemas.retrieval import RetrievalQueryRequest, RetrievalQueryResponse

router = APIRouter()


@router.post("/query", response_model=RetrievalQueryResponse)
def test_retrieval(request: RetrievalQueryRequest):
    chunks, execution_time_ms = retriever_service.retrieve(
        query=request.query,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        enable_reranking=request.enable_reranking,
        document_id_filter=request.document_id_filter,
    )
    return RetrievalQueryResponse(
        query=request.query,
        total_found=len(chunks),
        chunks=chunks,
        execution_time_ms=execution_time_ms,
    )
