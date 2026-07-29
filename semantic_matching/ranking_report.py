"""Evaluate semantic search results against human-reviewed relevance labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from chroma_store import ChromaJobStore
from matching_service import SearchCriteria, SemanticMatchingService


DEFAULT_CASES = [
    {
        "name": "remote_python_backend",
        "title": "Backend Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "location": "Remote",
        "experience_level": "mid level",
        "relevant_job_ids": [],
    },
    {
        "name": "machine_learning_engineer",
        "title": "Machine Learning Engineer",
        "skills": ["Python", "PyTorch", "NLP"],
        "location": "Remote",
        "experience_level": "entry level",
        "relevant_job_ids": [],
    },
]


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Return the fraction of top-k results judged relevant."""
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    if not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    return sum(job_id in relevant_ids for job_id in top_k) / k


def reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Return the reciprocal rank of the first relevant result."""
    for rank, job_id in enumerate(retrieved_ids, start=1):
        if job_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def evaluate(
    service: SemanticMatchingService,
    cases: list[dict[str, Any]],
    k_values: tuple[int, ...] = (5, 10),
) -> dict[str, Any]:
    """Run all cases and return per-query and aggregate metrics."""
    per_query = []

    for case in cases:
        criteria = SearchCriteria(
            title=case.get("title", ""),
            skills=tuple(case.get("skills", [])),
            location=case.get("location", ""),
            experience_level=case.get("experience_level", ""),
        )
        max_k = max(k_values)
        results = service.search(criteria, top_k=max_k)
        retrieved = [str(result["id"]) for result in results]
        relevant = {str(job_id) for job_id in case["relevant_job_ids"]}

        metrics = {
            f"precision_at_{k}": precision_at_k(retrieved, relevant, k)
            for k in k_values
        }
        metrics["reciprocal_rank"] = reciprocal_rank(retrieved, relevant)
        per_query.append(
            {
                "name": case.get("name", "unnamed_query"),
                "retrieved_job_ids": retrieved,
                "relevant_job_ids": sorted(relevant),
                **metrics,
            }
        )

    aggregate = {
        f"mean_precision_at_{k}": round(
            mean(item[f"precision_at_{k}"] for item in per_query), 4
        )
        if per_query
        else 0.0
        for k in k_values
    }
    aggregate["mean_reciprocal_rank"] = (
        round(mean(item["reciprocal_rank"] for item in per_query), 4)
        if per_query
        else 0.0
    )
    aggregate["query_count"] = len(per_query)
    return {"aggregate": aggregate, "queries": per_query}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="evaluation_cases.json")
    parser.add_argument("--output", default="ranking_report.json")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--create-template", action="store_true")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    if args.create_template:
        cases_path.write_text(json.dumps(DEFAULT_CASES, indent=2), encoding="utf-8")
        print(f"Created evaluation template: {cases_path}")
        return

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    store = ChromaJobStore(host=args.host, port=args.port)
    service = SemanticMatchingService(store)
    report = evaluate(service, cases)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))
    print(f"Saved full report to {output_path}")


if __name__ == "__main__":
    main()
