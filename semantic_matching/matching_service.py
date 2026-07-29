"""Semantic matching service for FastAPI integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentence_transformers import SentenceTransformer

from .chroma_store import ChromaJobStore


@dataclass(frozen=True)
class SearchCriteria:
    """Structured search input."""

    title: str = ""
    skills: tuple[str, ...] = ()
    location: str = ""
    experience_level: str = ""

    def to_embedding_text(self) -> str:
        """Combine search fields into one embedding string."""
        parts = [
            f"Desired role: {self.title}" if self.title else "",
            f"Skills: {', '.join(self.skills)}" if self.skills else "",
            f"Location: {self.location}" if self.location else "",
            (
                f"Experience level: {self.experience_level}"
                if self.experience_level
                else ""
            ),
        ]
        return " | ".join(part for part in parts if part)


class SemanticMatchingService:
    """Generate embeddings and retrieve ranked jobs."""

    def __init__(
        self,
        store: ChromaJobStore,
        model_name: str = "all-MiniLM-L6-v2",
        minimum_score: float = 0.35,
        model: Any | None = None,
        embedding_batch_size: int = 32,
    ) -> None:
        if embedding_batch_size <= 0:
            raise ValueError("embedding_batch_size must be greater than zero.")
        self.store = store
        self.model = model or SentenceTransformer(model_name)
        self.minimum_score = minimum_score
        self.embedding_batch_size = embedding_batch_size

    def index_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Embed and store normalized jobs."""
        if not jobs:
            return

        prepared_jobs = [prepare_job(job) for job in jobs]
        encoded = self.model.encode(
            [job["embedding_text"] for job in prepared_jobs],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=self.embedding_batch_size,
        )
        vectors = encoded.tolist() if hasattr(encoded, "tolist") else encoded
        self.store.upsert_jobs(prepared_jobs, vectors)

    def search(
        self,
        criteria: SearchCriteria,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for jobs above the configured score threshold."""
        query_text = criteria.to_embedding_text()
        if not query_text:
            raise ValueError("At least one search field is required.")

        encoded_query = self.model.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        query_vector = (
            encoded_query.tolist()
            if hasattr(encoded_query, "tolist")
            else list(encoded_query)
        )

        return [
            result
            for result in self.store.query_jobs(query_vector, top_k)
            if result["score"] >= self.minimum_score
        ]


def prepare_job(job: Any) -> dict[str, Any]:
    """Normalize backend or semantic-pipeline jobs before embedding."""
    if hasattr(job, "model_dump"):
        job = job.model_dump()
    elif hasattr(job, "dict"):
        job = job.dict()
    else:
        job = dict(job)

    tags = job.get("tags", job.get("skills", [])) or []
    description = job.get("desc", job.get("description", "")) or ""
    raw_id = str(job.get("job_id", job.get("id", "")))
    source = str(job.get("source", "remoteok")).lower().replace(" ", "")
    stable_id = raw_id if raw_id.startswith(f"{source}-") else f"{source}-{raw_id}"
    prepared = {
        **job,
        "id": stable_id,
        "skills": list(tags),
        "description": description,
        "date": job.get("date_posted", job.get("date", "")),
    }
    if not raw_id:
        raise ValueError("Job must contain job_id or id.")

    prepared["embedding_text"] = job.get("embedding_text") or " | ".join(
        part
        for part in [
            f"Title: {job.get('title', '')}",
            f"Company: {job.get('company', '')}",
            f"Location: {job.get('location', '')}",
            f"Skills: {', '.join(prepared['skills'])}",
            f"Description: {description}",
        ]
        if part.split(": ", 1)[-1]
    )
    return prepared
