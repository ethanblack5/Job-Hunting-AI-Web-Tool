"""ChromaDB helpers for semantic job search."""

from __future__ import annotations

from typing import Any

import chromadb


class ChromaJobStore:
    """Store and retrieve job embeddings."""

    def __init__(
        self,
        collection_name: str = "remoteok_jobs",
        host: str | None = None,
        port: int = 8000,
    ) -> None:
        self.client = (
            chromadb.HttpClient(host=host, port=port)
            if host
            else chromadb.PersistentClient(path="./chroma_data")
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_jobs(
        self,
        jobs: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update jobs by source ID."""
        if len(jobs) != len(embeddings):
            raise ValueError("Jobs and embeddings must have equal lengths.")

        self.collection.upsert(
            ids=[str(job["id"]) for job in jobs],
            embeddings=embeddings,
            documents=[job["embedding_text"] for job in jobs],
            metadatas=[
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "apply_url": job.get("apply_url", ""),
                }
                for job in jobs
            ],
        )

    def query_jobs(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Return ranked jobs with cosine similarity scores."""
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"],
        )

        ranked = []
        for job_id, metadata, document, distance in zip(
            result["ids"][0],
            result["metadatas"][0],
            result["documents"][0],
            result["distances"][0],
        ):
            ranked.append(
                {
                    "id": job_id,
                    "score": round(max(0.0, 1.0 - float(distance)), 4),
                    "title": metadata.get("title", ""),
                    "company": metadata.get("company", ""),
                    "location": metadata.get("location", ""),
                    "apply_url": metadata.get("apply_url", ""),
                    "embedding_text": document,
                }
            )

        return ranked
