import json
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.sql_models import EvaluationRecordModel
from app.retrieval.retriever import retriever_service
from app.llm.client import llm_client
from app.schemas.evaluation import (
    EvalTestCase,
    EvalItemResult,
    EvalSummaryMetrics,
    EvalRunResponse,
)

BENCHMARK_TEST_CASES = [
    EvalTestCase(
        id="TC-01",
        question="What is the mandatory password rotation policy and minimum length requirement?",
        expected_document="Enterprise_AI_Security_Policy.pdf",
        expected_topics=["password", "length", "rotation", "days"],
        is_unanswerable=False,
    ),
    EvalTestCase(
        id="TC-02",
        question="What are the procedures for rolling back a failed production deployment?",
        expected_document="Cloud_Infrastructure_SOP.pdf",
        expected_topics=["rollback", "deployment", "canary", "pipeline"],
        is_unanswerable=False,
    ),
    EvalTestCase(
        id="TC-03",
        question="What is the monthly internet stipend and home office equipment reimbursement limit?",
        expected_document="Employee_Remote_Work_Guide.pdf",
        expected_topics=["stipend", "reimbursement", "office", "equipment"],
        is_unanswerable=False,
    ),
    EvalTestCase(
        id="TC-04",
        question="What are the data classification levels defined by the organization?",
        expected_document="Enterprise_AI_Security_Policy.pdf",
        expected_topics=["public", "internal", "confidential", "restricted"],
        is_unanswerable=False,
    ),
    EvalTestCase(
        id="TC-05",
        question="What is the employee stock purchase plan (ESPP) discount percentage?",
        expected_document=None,
        expected_topics=[],
        is_unanswerable=True,  # Document does NOT contain ESPP info! Tests refusal/anti-hallucination
    ),
    EvalTestCase(
        id="TC-06",
        question="What is the caterer for the Friday company lunch and menu options?",
        expected_document=None,
        expected_topics=[],
        is_unanswerable=True,  # Out-of-scope question to verify refusal
    ),
]


class EvaluationService:
    def run_benchmark(self, db: Session) -> EvalRunResponse:
        results: List[EvalItemResult] = []
        start_all = time.time()

        for tc in BENCHMARK_TEST_CASES:
            t0 = time.time()

            # 1. Retrieval
            chunks, ret_latency = retriever_service.retrieve(
                query=tc.question,
                top_k=5,
                enable_reranking=True,
            )

            # 2. Context formatting
            formatted_context = retriever_service.format_context_for_prompt(chunks)

            # 3. Generation
            answer_schema = llm_client.generate_grounded_answer(
                query=tc.question,
                retrieved_chunks=chunks,
                formatted_context=formatted_context,
            )
            item_latency_ms = (time.time() - t0) * 1000.0

            # 4. Metric Computation
            retrieved_doc_names = list({c.filename for c in chunks})

            # Retrieval relevance
            if tc.is_unanswerable:
                # For unanswerable questions, chunks shouldn't contain high-confidence false matches
                retrieval_relevance = 1.0 if (not chunks or all(c.score < 0.6 for c in chunks)) else 0.7
            else:
                if tc.expected_document and tc.expected_document in retrieved_doc_names:
                    retrieval_relevance = 1.0
                elif any(any(top in c.content.lower() for top in tc.expected_topics) for c in chunks):
                    retrieval_relevance = 0.8
                else:
                    retrieval_relevance = 0.0

            # Citation presence
            citation_present = len(answer_schema.citations) > 0 or "[Doc:" in answer_schema.answer

            # Hallucination / Refusal test
            refusal_phrase_detected = any(
                phrase in answer_schema.answer.lower()
                for phrase in [
                    "not have enough information",
                    "do not have enough information",
                    "not contain enough information",
                    "insufficient information",
                    "provided documents do not",
                ]
            ) or answer_schema.insufficient_context

            is_hallucination_refusal = refusal_phrase_detected

            if tc.is_unanswerable:
                passed = is_hallucination_refusal
                groundedness_score = 1.0 if is_hallucination_refusal else 0.0
            else:
                passed = (retrieval_relevance >= 0.5) and citation_present and not refusal_phrase_detected
                groundedness_score = 1.0 if answer_schema.is_grounded and citation_present else 0.5

            item_result = EvalItemResult(
                id=tc.id,
                question=tc.question,
                expected_document=tc.expected_document,
                retrieved_documents=retrieved_doc_names,
                retrieval_relevance_score=round(retrieval_relevance, 2),
                groundedness_score=round(groundedness_score, 2),
                citation_present=citation_present,
                is_hallucination_refusal=is_hallucination_refusal,
                passed=passed,
                answer=answer_schema.answer,
                latency_ms=round(item_latency_ms, 2),
                notes="Refusal verified" if tc.is_unanswerable and is_hallucination_refusal else None,
            )
            results.append(item_result)

            # Save in database
            db_record = EvaluationRecordModel(
                question=tc.question,
                expected_doc=tc.expected_document or "None (Unanswerable)",
                retrieved_docs_json=json.dumps(retrieved_doc_names),
                answer=answer_schema.answer,
                relevance_score=retrieval_relevance,
                grounding_score=groundedness_score,
                citation_present=citation_present,
                is_hallucination_refusal=is_hallucination_refusal,
                latency_ms=item_latency_ms,
                status="passed" if passed else "failed",
            )
            db.add(db_record)

        db.commit()

        # Compute aggregate metrics
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        avg_retrieval = (sum(r.retrieval_relevance_score for r in results) / total) * 100.0
        avg_groundedness = (sum(r.groundedness_score for r in results) / total) * 100.0
        citation_cov = (sum(1 for r in results if r.citation_present) / total) * 100.0

        unanswerable_cases = [r for r in results if r.expected_document is None]
        refusal_acc = (
            (sum(1 for r in unanswerable_cases if r.is_hallucination_refusal) / len(unanswerable_cases)) * 100.0
            if unanswerable_cases
            else 100.0
        )
        avg_latency = sum(r.latency_ms for r in results) / total

        metrics = EvalSummaryMetrics(
            total_questions=total,
            passed_count=passed_count,
            retrieval_hit_rate_pct=round(avg_retrieval, 1),
            groundedness_avg_pct=round(avg_groundedness, 1),
            citation_coverage_pct=round(citation_cov, 1),
            refusal_accuracy_pct=round(refusal_acc, 1),
            avg_latency_ms=round(avg_latency, 1),
        )

        return EvalRunResponse(
            timestamp=datetime.utcnow(),
            metrics=metrics,
            results=results,
        )

    def get_history(self, db: Session, limit: int = 20) -> List[EvaluationRecordModel]:
        return db.query(EvaluationRecordModel).order_by(EvaluationRecordModel.created_at.desc()).limit(limit).all()


eval_service = EvaluationService()
