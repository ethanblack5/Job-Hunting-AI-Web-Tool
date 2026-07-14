"""
Vector DB insert/query functions
Basic CRUD + similarity search wrapper around the job_postings ChromaDB collection.
"""

from typing import Optional

from chroma_schema import REQUIRED_METADATA_FIELDS


def add_posting(collection, source_id: str, embedding: list, document: str, metadata: dict):
    """
    Insert (or upsert) a single job posting.
    - source_id becomes the Chroma record id (prevents duplicate postings from re-ingestion).
    - Uses upsert semantics so re-running the ingestion pipeline is safe/idempotent.
    """
    missing = [f for f in REQUIRED_METADATA_FIELDS if f not in metadata]
    if missing:
        raise ValueError(f"Missing required metadata fields: {missing}")

    collection.upsert(
        ids=[source_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata],
    )


def job_listing_to_chroma_record(job, embedding: list, source: str = "remoteok") -> dict:
    """
    Converts a job into the record shape add_postings_batch expects.

    Accepts either:
    - A dict shaped like the raw backend output (title, company, date_posted,
      location, min_salary, max_salary, apply_url, job_id, tags, desc, remoteok_url)
    - An instance of the backend's `JobListing` pydantic model directly (e.g. one
      value from the `job_dict` returned by `get_job_postings`)

    `embedding` must be supplied by the ML pipeline — this function does not compute it.

    Note: the backend's `min_salary`/`max_salary` are Optional[int] — None when the
    original posting didn't disclose a salary (RemoteOK sends 0 in that case, and the
    backend's `process_job` converts 0 -> None). Chroma metadata can't store null
    values, so we convert None back to 0 here on the way in.
    """
    # Normalize: pydantic model -> dict, so the rest of this function only deals with dicts
    if hasattr(job, "model_dump"):
        job = job.model_dump()
    elif hasattr(job, "dict"):
        job = job.dict()

    tags = job.get("tags", [])
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)

    return {
        "source_id": str(job["job_id"]),
        "embedding": embedding,
        "document": job.get("desc", ""),
        "metadata": {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "tags": tags_str,
            "location": job.get("location", ""),
            "apply_url": job.get("apply_url", ""),
            "remoteok_url": job.get("remoteok_url", ""),
            "source": source,
            "date_posted": job.get("date_posted", ""),
            "min_salary": job.get("min_salary") or 0,
            "max_salary": job.get("max_salary") or 0,
        },
    }


def add_postings_batch(collection, records: list[dict]):
    """
    Bulk insert. Each record must have: source_id, embedding, document, metadata.
    """
    ids, embeddings, documents, metadatas = [], [], [], []
    for r in records:
        missing = [f for f in REQUIRED_METADATA_FIELDS if f not in r["metadata"]]
        if missing:
            raise ValueError(f"Record {r.get('source_id')} missing fields: {missing}")
        ids.append(r["source_id"])
        embeddings.append(r["embedding"])
        documents.append(r["document"])
        metadatas.append(r["metadata"])

    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def similarity_search(
    collection,
    query_embedding: list,
    n_results: int = 5,
    location: Optional[str] = None,
    source: Optional[str] = None,
):
    """
    Run a similarity search against the collection, with optional metadata filters.
    query_embedding must come from the same embedding model used at insert time.
    """
    where = {}
    if location:
        where["location"] = location
    if source:
        where["source"] = source

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where or None,
    )


def get_by_id(collection, source_id: str):
    return collection.get(ids=[source_id])


def delete_posting(collection, source_id: str):
    collection.delete(ids=[source_id])


def count(collection) -> int:
    return collection.count()
