"""FastAPI endpoint that connects frontend search to semantic matching."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from chroma_store import ChromaJobStore
from matching_service import SearchCriteria, SemanticMatchingService


class JobSearchResult(BaseModel):
    """Frontend-compatible ranked job result."""

    job_id: str
    title: str
    company: str
    location: str
    apply_url: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


class SearchResponse(BaseModel):
    """Response returned by the semantic-search endpoint."""

    query: str
    result_count: int
    results: list[JobSearchResult]


@lru_cache(maxsize=1)
def get_matching_service() -> SemanticMatchingService:
    """Create one reusable model and ChromaDB connection per process."""
    store = ChromaJobStore(collection_name="remoteok_jobs")
    return SemanticMatchingService(
        store=store,
        model_name="all-MiniLM-L6-v2",
        minimum_score=0.35,
    )


def create_app() -> FastAPI:
    """Create the API application."""
    app = FastAPI(title="Job Hunting AI Search API")

    @app.get("/api/search", response_model=SearchResponse)
    def search_jobs(
        job_title: str | None = Query(None, min_length=2),
        skills: list[str] | None = Query(None),
        location: str | None = Query(None),
        experience_level: str | None = Query(None),
        limit: int = Query(20, ge=1, le=50),
        service: SemanticMatchingService = Depends(get_matching_service),
    ) -> SearchResponse:
        """Return jobs ranked by semantic similarity to user criteria."""
        criteria = SearchCriteria(
            title=(job_title or "").strip(),
            skills=tuple(skill.strip() for skill in skills or [] if skill.strip()),
            location=(location or "").strip(),
            experience_level=(experience_level or "").strip(),
        )

        query_text = criteria.to_embedding_text()
        if not query_text:
            raise HTTPException(
                status_code=422,
                detail="Provide at least one search criterion.",
            )

        try:
            matches = service.search(criteria, top_k=limit)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="The semantic search service is unavailable.",
            ) from exc

        results = [
            _to_search_result(match, rank)
            for rank, match in enumerate(matches, start=1)
        ]
        return SearchResponse(
            query=query_text,
            result_count=len(results),
            results=results,
        )

    return app


def _to_search_result(match: dict[str, Any], rank: int) -> JobSearchResult:
    """Convert retrieval output into the frontend response contract."""
    return JobSearchResult(
        job_id=str(match.get("id", "")),
        title=str(match.get("title", "")),
        company=str(match.get("company", "")),
        location=str(match.get("location", "")),
        apply_url=str(match.get("apply_url", "")),
        similarity_score=float(match.get("score", 0.0)),
        rank=rank,
    )


app = create_app()
