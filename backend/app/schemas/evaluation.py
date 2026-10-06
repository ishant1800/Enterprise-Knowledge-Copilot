from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class EvalTestCase(BaseModel):
    id: str
    question: str
    expected_document: Optional[str] = None
    expected_topics: List[str] = []
    is_unanswerable: bool = False  # To test hallucination prevention / refusal


class EvalItemResult(BaseModel):
    id: str
    question: str
    expected_document: Optional[str] = None
    retrieved_documents: List[str] = []
    retrieval_relevance_score: float  # 0.0 to 1.0
    groundedness_score: float  # 0.0 to 1.0
    citation_present: bool
    is_hallucination_refusal: bool
    passed: bool
    answer: str
    latency_ms: float
    notes: Optional[str] = None


class EvalSummaryMetrics(BaseModel):
    total_questions: int
    passed_count: int
    retrieval_hit_rate_pct: float
    groundedness_avg_pct: float
    citation_coverage_pct: float
    refusal_accuracy_pct: float
    avg_latency_ms: float


class EvalRunResponse(BaseModel):
    timestamp: datetime
    metrics: EvalSummaryMetrics
    results: List[EvalItemResult]
