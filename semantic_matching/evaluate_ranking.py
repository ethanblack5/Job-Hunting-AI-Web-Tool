"""Evaluate ranking quality with Precision@K and MRR."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from chroma_store import ChromaJobStore
from matching_service import SearchCriteria, SemanticMatchingService


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Calculate Precision@K."""
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    top_ids = retrieved_ids[:k]
    return sum(job_id in relevant_ids for job_id in top_ids) / k


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Calculate reciprocal rank for one query."""
    for rank, job_id in enumerate(retrieved_ids, start=1):
        if job_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def evaluate_cases(
    service: SemanticMatchingService,
    cases: list[dict[str, Any]],
    k: int = 5,
) -> dict[str, float]:
    """Evaluate human-reviewed query cases."""
    precision_scores = []
    reciprocal_ranks = []

    for case in cases:
        criteria = SearchCriteria(
            title=case.get("title", ""),
            skills=tuple(case.get("skills", [])),
            location=case.get("location", ""),
            experience_level=case.get("experience_level", ""),
        )
        results = service.search(criteria, top_k=max(k, 10))
        retrieved_ids = [str(item["id"]) for item in results]
        relevant_ids = {str(item) for item in case["relevant_job_ids"]}

        precision_scores.append(
            precision_at_k(retrieved_ids, relevant_ids, k)
        )
        reciprocal_ranks.append(
            reciprocal_rank(retrieved_ids, relevant_ids)
        )

    count = len(cases)
    return {
        f"precision_at_{k}": (
            round(sum(precision_scores) / count, 4) if count else 0.0
        ),
        "mean_reciprocal_rank": (
            round(sum(reciprocal_ranks) / count, 4) if count else 0.0
        ),
        "query_count": count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="evaluation_cases.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    with Path(args.cases).open(encoding="utf-8") as file:
        cases = json.load(file)

    store = ChromaJobStore(host=args.host, port=args.port)
    service = SemanticMatchingService(store)
    print(json.dumps(evaluate_cases(service, cases, args.k), indent=2))


if __name__ == "__main__":
    main()
