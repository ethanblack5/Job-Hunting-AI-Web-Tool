"""Tests for the FastAPI semantic-search endpoint."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from fastapi.testclient import TestClient

from search_api import create_app, get_matching_service


class FakeMatchingService:
    """Deterministic replacement for the model and ChromaDB in tests."""

    def __init__(self, results: list[dict[str, Any]] | None = None) -> None:
        self.results = results or []
        self.last_criteria = None
        self.last_top_k = None

    def search(self, criteria, top_k: int = 10):
        self.last_criteria = criteria
        self.last_top_k = top_k
        return self.results[:top_k]


def build_client(service: FakeMatchingService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_matching_service] = lambda: service
    return TestClient(app)


def test_search_returns_ranked_frontend_response() -> None:
    service = FakeMatchingService(
        [
            {
                "id": "101",
                "title": "Machine Learning Engineer",
                "company": "Example AI",
                "location": "Remote",
                "apply_url": "https://example.com/jobs/101",
                "score": 0.91,
            },
            {
                "id": "102",
                "title": "Python Data Engineer",
                "company": "Data Works",
                "location": "United States",
                "apply_url": "https://example.com/jobs/102",
                "score": 0.82,
            },
        ]
    )
    client = build_client(service)

    response = client.get(
        "/api/search",
        params=[
            ("job_title", "Machine Learning Engineer"),
            ("skills", "Python"),
            ("skills", "PyTorch"),
            ("location", "Remote"),
            ("limit", "5"),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result_count"] == 2
    assert payload["results"][0]["rank"] == 1
    assert payload["results"][0]["job_id"] == "101"
    assert payload["results"][0]["similarity_score"] == 0.91
    assert service.last_criteria.skills == ("Python", "PyTorch")
    assert service.last_top_k == 5


def test_search_requires_at_least_one_criterion() -> None:
    client = build_client(FakeMatchingService())

    response = client.get("/api/search")

    assert response.status_code == 422
    assert response.json()["detail"] == "Provide at least one search criterion."


def test_search_validates_limit() -> None:
    client = build_client(FakeMatchingService())

    response = client.get(
        "/api/search",
        params={"job_title": "Developer", "limit": 100},
    )

    assert response.status_code == 422


def test_search_returns_503_when_retrieval_fails() -> None:
    failing_service = Mock()
    failing_service.search.side_effect = RuntimeError("ChromaDB unavailable")
    app = create_app()
    app.dependency_overrides[get_matching_service] = lambda: failing_service
    client = TestClient(app)

    response = client.get(
        "/api/search",
        params={"job_title": "Backend Engineer"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The semantic search service is unavailable."
    )
