"""
Schema design for job postings collection.

Design notes:
- ChromaDB stores vectors + associated metadata + a document string per record.
- We use ChromaDB's PersistentClient in "embedded mode"
- Embedding dimension is NOT hardcoded.
  Chroma infers it from whatever vectors are passed in on `.add()`.
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings

# Client setup — embedded mode (local persistent storage, no separate server)

DB_PATH = Path(__file__).parent / "chroma_store"


def get_client(path: str = str(DB_PATH)) -> chromadb.PersistentClient:
    """
    Returns a local, embedded ChromaDB client backed by on-disk storage.
    No server/daemon required — this is what "embedded mode" means in
    Chroma's docs.
    """
    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False),
    )


COLLECTION_NAME = "job_postings"

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


def get_or_create_collection(client=None):
    """Creates the job_postings collection. Uses cosine similarity,
    which is standard for text-embedding similarity search."""
    client = client or get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
