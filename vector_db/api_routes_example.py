"""
Example FastAPI route wiring the retrieval layer in.

This is a minimal example -- once Ethan's backend contract and router
structure are confirmed, this route (or its equivalent) should live
wherever his FastAPI app actually organizes its routes, not necessarily
in vector_db/.
"""

from fastapi import APIRouter, Query

from chroma_schema import get_client, get_or_create_collection
from retrieval import retrieve_for_api

router = APIRouter()

_client = get_client()
_collection = get_or_create_collection(_client)


@router.get("/search")
def search(
    q: str = Query(..., description="User's search query"),
    top_n: int = Query(10, ge=1, le=50),
    location: str | None = None,
    source: str | None = None,
):
    return retrieve_for_api(_collection, q, top_n=top_n, location=location, source=source)
