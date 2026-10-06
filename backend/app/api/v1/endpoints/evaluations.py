from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.eval_service import eval_service
from app.schemas.evaluation import EvalRunResponse

router = APIRouter()


@router.post("/run", response_model=EvalRunResponse)
def run_evaluation(db: Session = Depends(get_db)):
    return eval_service.run_benchmark(db)


@router.get("/history")
def get_evaluation_history(limit: int = 20, db: Session = Depends(get_db)):
    records = eval_service.get_history(db, limit=limit)
    return [
        {
            "id": r.id,
            "question": r.question,
            "expected_doc": r.expected_doc,
            "answer": r.answer,
            "relevance_score": r.relevance_score,
            "grounding_score": r.grounding_score,
            "citation_present": r.citation_present,
            "is_hallucination_refusal": r.is_hallucination_refusal,
            "latency_ms": r.latency_ms,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in records
    ]
