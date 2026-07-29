"""Semantic matching service for FastAPI integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentence_transformers import SentenceTransformer

from chroma_store import ChromaJobStore


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
    ) -> None:
        self.store = store
        self.model = SentenceTransformer(model_name)
        self.minimum_score = minimum_score

    def index_jobs(self, jobs: list[dict[str, Any]]) -> None:
        """Embed and store normalized jobs."""
        if not jobs:
            return

        vectors = self.model.encode(
            [job["embedding_text"] for job in jobs],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        self.store.upsert_jobs(jobs, vectors)

    def search(
        self,
        criteria: SearchCriteria,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for jobs above the configured score threshold."""
        query_text = criteria.to_embedding_text()
        if not query_text:
            raise ValueError("At least one search field is required.")

        query_vector = self.model.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0].tolist()

        return [
            result
            for result in self.store.query_jobs(query_vector, top_k)
            if result["score"] >= self.minimum_score
        ]
