"""
Vector DB insert/query functions
Similarity search
"""

import time
from typing import Optional

try:
    from .chroma_logging import log_index_size, log_query
    from .chroma_schema import REQUIRED_METADATA_FIELDS
except ImportError:  # Support running legacy scripts from vector_db/.
    from chroma_logging import log_index_size, log_query
    from chroma_schema import REQUIRED_METADATA_FIELDS

DEFAULT_UPSERT_BATCH_SIZE = 100
MAX_QUERY_RESULTS = 50


def add_posting(
    collection,
    source_id: str,
    embedding: list,
    document: str,
    metadata: dict,
):
    """
    Insert (or upsert) a single job posting.
    - source_id becomes the Chroma record id.
    - Uses upsert semantics so re-running the ingestion
      pipeline is safe/idempotent.
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
    log_index_size(collection)


def job_listing_to_chroma_record(
    job,
    embedding: list,
    source: str = "remoteok",
) -> dict:
    """
    Convert a job into the record shape expected by
    add_postings_batch.

    """
    if hasattr(job, "model_dump"):
        job = job.model_dump()
    elif hasattr(job, "dict"):
        job = job.dict()

    source_id = job.get("id", job.get("job_id"))
    if source_id is None:
        raise ValueError("Job must contain job_id or id.")

    tags = job.get("tags", job.get("skills", []))
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
    description = job.get("desc", job.get("description", ""))
    date_posted = job.get("date_posted", job.get("date", ""))
    salary = job.get("cleaned_salary", job.get("salary", "")) or ""

    return {
        "source_id": str(source_id),
        "embedding": embedding,
        "document": job.get("embedding_text") or description,
        "metadata": {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "tags": tags_str,
            "location": job.get("location", ""),
            "apply_url": job.get("apply_url", ""),
            "remoteok_url": job.get("remoteok_url", ""),
            "source": source,
            "date_posted": date_posted,
            "min_salary": job.get("min_salary") or 0,
            "max_salary": job.get("max_salary") or 0,
            "salary": salary,
            "description": description,
            "role_type": job.get("role_type") or "",
        },
    }


def add_postings_batch(
    collection,
    records: list[dict],
    batch_size: int = DEFAULT_UPSERT_BATCH_SIZE,
):
    """
    Bulk insert. Each record must have:
    source_id, embedding, document, metadata.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")
    if not records:
        return

    ids, embeddings, documents, metadatas = [], [], [], []
    for r in records:
        missing = [
            f
            for f in REQUIRED_METADATA_FIELDS
            if f not in r["metadata"]
        ]
        if missing:
            raise ValueError(
                f"Record {r.get('source_id')} missing fields: {missing}"
            )
        ids.append(r["source_id"])
        embeddings.append(r["embedding"])
        documents.append(r["document"])
        metadatas.append(r["metadata"])

    for start in range(0, len(records), batch_size):
        stop = start + batch_size
        collection.upsert(
            ids=ids[start:stop],
            embeddings=embeddings[start:stop],
            documents=documents[start:stop],
            metadatas=metadatas[start:stop],
        )
    log_index_size(collection)


def similarity_search(
    collection,
    query_embedding: list,
    n_results: int = 5,
    location: Optional[str] = None,
    source: Optional[str] = None,
    log_query_activity: bool = True,
    include: Optional[list[str]] = None,
):
    """
    Run a similarity search against the collection, with
    optional metadata filters.
    query_embedding must come from the same embedding model
    used at insert time.
    """
    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    collection_size = collection.count()
    effective_results = min(
        n_results,
        MAX_QUERY_RESULTS,
        collection_size,
    )
    if effective_results == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    where = {}
    if location:
        where["location"] = location
    if source:
        where["source"] = source

    start = time.perf_counter()
    query_arguments = {
        "query_embeddings": [query_embedding],
        "n_results": effective_results,
        "where": where or None,
    }
    if include is not None:
        query_arguments["include"] = include

    results = collection.query(
        **query_arguments,
    )
    elapsed = time.perf_counter() - start

    if log_query_activity:
        log_query(
            collection,
            len(results.get("ids", [[]])[0]),
            elapsed,
            source=source,
            location=location,
        )

    return results


def get_by_id(collection, source_id: str):
    return collection.get(ids=[source_id])


def delete_posting(collection, source_id: str):
    collection.delete(ids=[source_id])
    log_index_size(collection)


def count(collection) -> int:
    return collection.count()
