"""
Schema design for job postings collection.

Notes:
- ChromaDB stores vectors + associated metadata + a document string per record.
- We use ChromaDB's PersistentClient in "embedded mode"
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings

# Client setup

DB_PATH = Path(__file__).resolve().parent / "chroma_store"


def get_client(path: str = str(DB_PATH)) -> chromadb.PersistentClient:
    """
    Returns a local, embedded ChromaDB client backed by on-disk storage.
    """
    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False),
    )


# This collection has a stable 384-dimensional MiniLM schema. It intentionally
# uses a new name so older test/fallback embeddings are never mixed into it.
COLLECTION_NAME = "job_postings_v2"

REQUIRED_METADATA_FIELDS = [
    "title",
    "company",
    "date_posted",
    "location",
    "min_salary",
    "max_salary",
    "apply_url",
    "tags",
    "remoteok_url",
    "source",
]


def get_or_create_collection(client=None, collection_name: str = COLLECTION_NAME):
    """Creates the job_postings collection. Uses cosine similarity,
    which is standard for text-embedding similarity search."""
    client = client or get_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
        },
    )
