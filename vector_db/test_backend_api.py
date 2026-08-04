"""Goal and summary:

These tests improve coverage of the backend API by verifying that job postings
from RemoteOK are cleaned and normalized correctly, user search requests are
validated, external API failures are handled gracefully, and search results are
returned in the expected format. The tests also verify that the job index is
automatically refreshed when the database is empty. The tests use fakes instead
of RemoteOK and embedding-model network dependencies.

"""

from unittest.mock import MagicMock

import pytest
import requests
from fastapi.testclient import TestClient

import fastapi_backend.api as api


class FakeResponse:
    def __init__(self, payload=None):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.fixture
def client():
    api.index_last_updated = None
    with TestClient(api.app) as test_client:
        yield test_client
    api.index_last_updated = None


def remoteok_job(**overrides):
    job = {
        "id": "123",
        "position": "Python Backend Engineer",
        "company": "Acme",
        "date": "2026-07-30T12:00:00Z",
        "location": "  Remote, ",
        "salary_min": 100000,
        "salary_max": 130000,
        "apply_url": "https://example.com/apply",
        "tags": ["Python", "Backend", "python"],
        "description": "Build APIs &amp; services.<br>",
        "url": "https://remoteok.com/jobs/123",
    }
    job.update(overrides)
    return job


def test_fetch_job_postings_filters_and_normalizes_remoteok_data(monkeypatch):
    payload = [
        {"legal": "RemoteOK attribution record"},
        remoteok_job(),
        remoteok_job(id="124", position="Designer", tags=["design"]),
        "malformed record",
    ]
    monkeypatch.setattr(
        api.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    jobs = api.fetch_job_postings(
        query_tags="python",
        position="backend",
        date="2026-07-30",
    )

    assert len(jobs) == 1
    assert jobs[0].job_id == "remoteok-123"
    assert jobs[0].date_posted == "2026-07-30"
    assert jobs[0].location == "Remote"
    assert jobs[0].tags == ["backend", "python"]
    assert jobs[0].desc == "Build APIs & services."


def test_fetch_job_postings_maps_timeout_to_gateway_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("too slow")

    monkeypatch.setattr(api.requests, "get", timeout)

    with pytest.raises(api.HTTPException) as exc_info:
        api.fetch_job_postings()

    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == "Remote OK request timed out."


def test_fetch_job_postings_rejects_non_list_payload(monkeypatch):
    monkeypatch.setattr(
        api.requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"jobs": []}),
    )

    with pytest.raises(api.HTTPException) as exc_info:
        api.fetch_job_postings()

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Unexpected response format."


def test_process_job_extracts_missing_salary_and_cleans_fields():
    job = api.JobListing(
        title="Engineer",
        company="Acme",
        date_posted="2026-07-30T15:00:00Z",
        location="  New   York, ",
        min_salary="0",
        max_salary="0",
        apply_url="https://example.com",
        job_id="1",
        tags=[" Python ", "PYTHON", "AWS"],
        desc="Base salary: $80k-$120k.",
        remoteok_url="https://remoteok.com/1",
    )

    processed = api.process_job(job)

    assert processed.date_posted == "2026-07-30"
    assert processed.location == "New York"
    assert processed.tags == ["aws", "python"]
    assert processed.min_salary == "$80,000"
    assert processed.max_salary == "$120,000"
    assert processed.cleaned_salary == "$80,000 - $120,000"


def test_search_rejects_all_empty_fields(client):
    response = client.post(
        "/api/search",
        json={
            "job_title": " ",
            "skills": [],
            "location": " ",
            "experience_level": " ",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one search field is required."


def test_search_request_validates_top_n_range(client):
    response = client.post(
        "/api/search",
        json={"job_title": "Engineer", "top_n": 51},
    )

    assert response.status_code == 422


def test_search_returns_service_unavailable_when_matching_fails(
    client,
    monkeypatch,
):
    def unavailable_service():
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(api, "get_matching_service", unavailable_service)

    response = client.post(
        "/api/search",
        json={"job_title": "Engineer", "location": ""},
    )

    assert response.status_code == 503
    assert "model unavailable" in response.json()["detail"]


def test_search_returns_results_and_skill_analytics(client, monkeypatch):
    service = MagicMock()
    service.store.collection.count.return_value = 2
    service.search.return_value = [
        {
            "id": "remoteok-1",
            "score": 0.9,
            "title": "Python Engineer",
            "company": "Acme",
            "location": "Remote",
            "salary": None,
            "role_type": None,
            "date_listed": None,
            "description": "Build services.",
            "skills": ["python", "aws"],
            "apply_url": "https://example.com/1",
        },
        {
            "id": "remoteok-2",
            "score": 0.8,
            "title": "Data Engineer",
            "company": "Beta",
            "location": "Remote",
            "salary": None,
            "role_type": None,
            "date_listed": None,
            "description": "Build pipelines.",
            "skills": ["python", "sql"],
            "apply_url": "https://example.com/2",
        },
    ]
    monkeypatch.setattr(api, "get_matching_service", lambda: service)

    response = client.post(
        "/api/search",
        json={
            "job_title": " Engineer ",
            "skills": [" python ", ""],
            "location": " remote ",
            "top_n": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_count"] == 2
    assert body["analytics"]["skill_frequency"][0] == {
        "skill": "python",
        "count": 2,
    }
    criteria = service.search.call_args.args[0]
    assert criteria.title == "Engineer"
    assert criteria.skills == ("python",)
    assert criteria.location == "remote"
    assert service.search.call_args.kwargs["top_k"] == 2


def test_search_refreshes_remoteok_when_collection_is_empty(
    client,
    monkeypatch,
):
    service = MagicMock()
    service.store.collection.count.return_value = 0
    service.search.return_value = []
    job = api.JobListing(
        title="Engineer",
        company="Acme",
        date_posted="2026-07-30",
        location="Remote",
        apply_url="https://example.com",
        job_id="remoteok-1",
        tags=["python"],
        desc="Build services.",
        remoteok_url="https://remoteok.com/1",
    )
    monkeypatch.setattr(api, "get_matching_service", lambda: service)
    monkeypatch.setattr(api, "fetch_job_postings", lambda: [job])

    response = client.post(
        "/api/search",
        json={"job_title": "Engineer", "location": ""},
    )

    assert response.status_code == 200
    service.index_jobs.assert_called_once_with([job])
    service.search.assert_called_once()
    assert response.json()["index_last_updated"] is not None
