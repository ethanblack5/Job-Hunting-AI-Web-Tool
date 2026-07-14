"""Create a small Sentence Transformer semantic-ranking baseline."""

from __future__ import annotations

import argparse
import json
from typing import Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_MODEL = "all-MiniLM-L6-v2"


def rank_jobs(
    query: str,
    jobs: list[dict[str, Any]],
    model_name: str = DEFAULT_MODEL,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Rank normalized jobs against a natural-language search query."""
    if not jobs:
        return []

    model = SentenceTransformer(model_name)
    job_texts = [job["embedding_text"] for job in jobs]
    job_vectors = model.encode(job_texts, normalize_embeddings=True)
    query_vector = model.encode([query], normalize_embeddings=True)

    scores = cosine_similarity(query_vector, job_vectors)[0]
    ranked_indices = scores.argsort()[::-1][:top_k]

    return [
        {
            "rank": rank,
            "score": round(float(scores[index]), 4),
            "id": jobs[index]["id"],
            "title": jobs[index]["title"],
            "company": jobs[index]["company"],
            "location": jobs[index]["location"],
            "skills": jobs[index]["skills"],
            "apply_url": jobs[index]["apply_url"],
        }
        for rank, index in enumerate(ranked_indices, start=1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        nargs="?",
        default="Python machine learning engineer with API and cloud experience",
    )
    parser.add_argument("--input", default="remoteok_jobs_normalized.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as file:
        jobs = json.load(file)

    results = rank_jobs(args.query, jobs, args.model, args.top_k)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
