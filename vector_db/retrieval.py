"""
Retrieval layer: embeds a user query, runs similarity search against
Chroma, and returns ranked results.

Two things in this file depend on contracts that aren't finalized yet:

1. MODEL_NAME / preprocess_query() -- depends on Jawwad's confirmed
   Sentence Transformer model + preprocessing steps used on the
   indexing side. THIS MUST MATCH EXACTLY or similarity scores are
   meaningless (garbage in, garbage out -- the query embedding has to
   live in the same vector space as the indexed embeddings).

2. to_api_response() -- depends on Ethan's FastAPI response format
   contract. Everything else in this file returns an internal,
   self-explanatory dict shape; to_api_response() is the ONLY place
   that needs to change once the real contract is confirmed.

Until both are confirmed, this file uses reasonable placeholders so
retrieval logic can be built, tested, and reused right now instead of
sitting blocked.
"""

from typing import Optional

from sentence_transformers import SentenceTransformer

from chroma_ops import similarity_search

# --- 1. MODEL CONTRACT (placeholder until Jawwad confirms) -----------------
# TODO: replace with Jawwad's confirmed model name once finalized.
# This MUST be the exact same model used when embeddings were built on
# the indexing side, or query embeddings won't line up with indexed ones.
MODEL_NAME = "all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """
    Lazily loads the embedding model once and reuses it -- loading a
    Sentence Transformer model is slow, so we don't want to do it on
    every single query.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def preprocess_query(raw_query: str) -> str:
    """
    Normalizes a raw user query before embedding it.

    TODO: this MUST match whatever preprocessing Jawwad's indexing
    pipeline applies (lowercasing, whitespace handling, stripping
    special characters, etc). Right now this is a reasonable guess
    (basic lowercase + strip), not a confirmed contract.
    """
    return raw_query.strip().lower()


def embed_query(raw_query: str) -> list:
    """Preprocesses and embeds a single user query."""
    query = preprocess_query(raw_query)
    return get_model().encode(query).tolist()


# --- 2. Core retrieval logic (contract-independent, safe to build now) -----

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

    This internal shape is intentionally NOT the final API response --
    see to_api_response() below for that conversion.
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


# --- 3. API response contract (placeholder until Ethan confirms) ----------

def to_api_response(raw_query: str, ranked_results: list[dict]) -> dict:
    """
    Converts internal ranked results into the shape the FastAPI backend
    expects.

    TODO: replace this with Ethan's confirmed response contract.
    This is a reasonable placeholder shape, NOT a confirmed format --
    field names, nesting, and included fields may all need to change.
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
    This is what the FastAPI route should actually call.
    """
    ranked_results = retrieve(collection, raw_query, top_n=top_n, location=location, source=source)
    return to_api_response(raw_query, ranked_results)
