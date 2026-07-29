"""ChromaDB helpers for semantic job search."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from vector_db.chroma_ops import (
    DEFAULT_UPSERT_BATCH_SIZE,
    add_postings_batch,
    job_listing_to_chroma_record,
    similarity_search,
)
from vector_db.chroma_schema import (
    COLLECTION_NAME,
    DB_PATH,
    get_client,
    get_or_create_collection,
)


class ChromaJobStore:
    """Semantic-matching adapter for the shared vector_db collection."""

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        host: str | None = None,
        port: int = 8000,
        path: str | Path | None = None,
        client: Any | None = None,
        batch_size: int = DEFAULT_UPSERT_BATCH_SIZE,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")
        self.batch_size = batch_size
        if client is not None:
            self.client = client
        elif host:
            self.client = chromadb.HttpClient(host=host, port=port)
        else:
            self.client = get_client(str(path or DB_PATH))

        self.collection = get_or_create_collection(
            self.client,
            collection_name=collection_name,
        )

    def upsert_jobs(
        self,
        jobs: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update jobs by source ID."""
        if len(jobs) != len(embeddings):
            raise ValueError("Jobs and embeddings must have equal lengths.")

        records = [
            job_listing_to_chroma_record(job, embedding, source="remoteok")
            for job, embedding in zip(jobs, embeddings)
        ]
        add_postings_batch(
            self.collection,
            records,
            batch_size=self.batch_size,
        )

    def query_jobs(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Return ranked jobs with cosine similarity scores."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        if self.collection.count() == 0:
            return []

        result = similarity_search(
            self.collection,
            query_embedding,
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        ranked = []
        for job_id, metadata, distance in zip(
            result["ids"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            skills = [
                skill
                for skill in metadata.get("tags", "").split(",")
                if skill
            ]
            ranked.append(
                {
                    "id": job_id,
                    "score": round(max(0.0, 1.0 - float(distance)), 4),
                    "title": metadata.get("title", ""),
                    "company": metadata.get("company", ""),
                    "location": metadata.get("location", ""),
                    "apply_url": metadata.get("apply_url", ""),
                    "salary": metadata.get("salary") or None,
                    "date_listed": metadata.get("date_posted") or None,
                    "description": metadata.get("description") or "",
                    "skills": skills,
                    "role_type": metadata.get("role_type") or None,
                }
            )

        return ranked
