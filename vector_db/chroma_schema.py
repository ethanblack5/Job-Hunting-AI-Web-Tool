"""
Schema design for job postings collection.

Design notes:
- ChromaDB stores vectors + associated metadata + a document string per record.
- We use ChromaDB's PersistentClient in "embedded mode" 
- Embedding dimension is NOT hardcoded. Chroma infers it from whatever vectors are
  passed in on `.add()`.
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path


# Client setup — embedded mode (local persistent storage, no separate server)

DB_PATH = Path(__file__).parent / "chroma_store"

def get_client(path: str = str(DB_PATH)) -> chromadb.PersistentClient:
    """
    Returns a local, embedded ChromaDB client backed by on-disk storage.
    No server/daemon required — this is what "embedded mode" means in Chroma's docs.
    """
    return chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))


COLLECTION_NAME = "job_postings"

# 
# Metadata schema for each job posting record
# ---------------------------------------------------------------------------
# ChromaDB metadata values must be str, int, float, or bool (no nested dicts/lists).
# For list-like fields (skills), we store a comma-joined string AND keep the parsed
# list available at the application layer — Chroma can't filter on list membership
# natively pre-1.x, so comma-joined + substring/`$contains` filtering is the practical
# approach for a small-scale prototype like this.
#
# Field           Type    Notes
# --------------- ------- ------------------------------------------------------------
# source_id       str     Unique job ID (maps to backend's `job_id`). Used as the Chroma
#                          record `id` (primary key) to prevent duplicate postings.
# title           str     Job title, e.g. "Senior Data Engineer" — matches backend `title`
# company         str     Employer name — matches backend `company`
# tags            str     Comma-joined skill/tag list, e.g. "python,sql,aws,fhir".
#                          Backend's `tags` field is a list — Chroma metadata can't store
#                          nested lists, so we comma-join on the way in.
# location        str     "City, ST" or "Remote" — matches backend `location`
# apply_url       str     URL to the original posting — matches backend `apply_url`
# remoteok_url    str     Link to the posting on remoteok.com itself — matches backend
#                          `remoteok_url` (required for RemoteOK API attribution — see
#                          their Terms of Service)
# source          str     Which board it came from, e.g. "remoteok", "indeed", "linkedin"
#                          (not in backend model yet; hardcode "remoteok" for now since
#                          that's the only integration — keeps us ready for more sources later)
# date_posted     str     Date string, YYYY-MM-DD — matches backend `date_posted`
# min_salary      int     matches backend `min_salary`; backend uses None for "not
#                          disclosed" — we convert None to 0 since Chroma metadata
#                          can't store null values
# max_salary      int     matches backend `max_salary`; same None-to-0 handling
#
# The `document` field (separate from metadata) stores the raw job description text
# (backend's `desc`) — useful for debugging/display and potential future re-embedding.

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
    """Creates (or fetches) the job_postings collection. Uses cosine similarity,
    which is standard for text-embedding similarity search."""
    client = client or get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
