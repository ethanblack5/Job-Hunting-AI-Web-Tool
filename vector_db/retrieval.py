"""
Retrieval layer: embeds a user query, runs similarity search against
Chroma, and returns ranked results.
"""

import math
import re
from typing import Optional

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - exercised when dependency is absent
    SentenceTransformer = None

from chroma_ops import similarity_search

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 64

_model: Optional[object] = None


class FallbackEmbeddingModel:
    """Deterministic local embedding model used when sentence-transformers is unavailable."""

    def encode(self, text: str) -> list[float]:
        tokens = [token for token in re.split(r"\W+", text.lower()) if token]
        vector = [0.0] * EMBEDDING_DIMENSION

        for token in tokens:
            index = abs(hash(token)) % EMBEDDING_DIMENSION
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def get_model() -> object:
    """
    Lazily loads the embedding model once and reuses it for subsequent queries.
    If sentence-transformers is not installed, a deterministic fallback encoder is used.
    """
    global _model
    if _model is None:
        if SentenceTransformer is not None:
            _model = SentenceTransformer(MODEL_NAME)
        else:
            _model = FallbackEmbeddingModel()
    return _model


def preprocess_query(raw_query: str) -> str:
    """
    Normalizes a raw user query before embedding it.
    """
    return raw_query.strip().lower()


def embed_query(raw_query: str) -> list:
    """Preprocesses and embeds a single user query."""
    query = preprocess_query(raw_query)
    return get_model().encode(query).tolist()

def retrieve(
    collection,
    raw_query: str,
    top_n: int = 10,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> list[dict]:
    """
    Embeds the query, runs similarity search, and returns ranked
    results in an internal shape:

        [{"id": ..., "document": ..., "metadata": {...}, "similarity_score": ...}, ...]
    """
    query_embedding = embed_query(raw_query)

    results = similarity_search(
        collection,
        query_embedding,
        n_results=top_n,
        location=location,
        source=source,
    )

    ranked = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for record_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        # Chroma's collection is configured with hnsw:space=cosine (see
        # chroma_schema.py), so distance is cosine distance in [0, 2].
        # Convert to a similarity score in roughly [0, 1] for readability
        # (1 = identical direction, 0 = unrelated, negative = opposite).
        similarity_score = 1 - distance

        ranked.append({
            "id": record_id,
            "document": document,
            "metadata": metadata,
            "similarity_score": similarity_score,
        })

    return ranked


def to_api_response(raw_query: str, ranked_results: list[dict]) -> dict:
    """
    Converts internal ranked results into the shape the FastAPI backend
    expects.
    """
    return {
        "query": raw_query,
        "results": [
            {
                "job_id": r["id"],
                "title": r["metadata"].get("title"),
                "company": r["metadata"].get("company"),
                "location": r["metadata"].get("location"),
                "apply_url": r["metadata"].get("apply_url"),
                "similarity_score": round(r["similarity_score"], 4),
            }
            for r in ranked_results
        ],
        "count": len(ranked_results),
    }


def retrieve_for_api(
    collection,
    raw_query: str,
    top_n: int = 10,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> dict:
    """
    Convenience function combining retrieve() + to_api_response().
    Returns results in the shape the FastAPI backend expects.
    """
    ranked_results = retrieve(collection, raw_query, top_n=top_n, location=location, source=source)
    return to_api_response(raw_query, ranked_results)
