"""Goal and summary:

These tests improve coverage of the semantic matching service by verifying that
search criteria are converted into embedding text correctly, job data is
normalized before indexing, embeddings are generated in configurable batches,
and semantic search returns only relevant results based on the minimum
similarity score. The tests also verify duplicate job handling, input
validation, and error handling when ChromaDB is unavailable. The tests avoid
model and network dependencies.

"""

from unittest.mock import MagicMock

import pytest

from semantic_matching.matching_service import (
    SearchCriteria,
    SemanticMatchingService,
    prepare_job,
)


class FakeArray(list):
    """Minimal ndarray-like value returned by the fake embedding model."""

    def __getitem__(self, index):
        value = super().__getitem__(index)
        return FakeArray(value) if isinstance(value, list) else value

    def tolist(self):
        return list(self)


class RecordingModel:
    """Record embedding calls and return deterministic vectors."""

    def __init__(self, vectors):
        self.vectors = vectors
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return FakeArray(self.vectors)


def test_search_criteria_builds_embedding_text_from_populated_fields():
    criteria = SearchCriteria(
        title="Backend Engineer",
        skills=("Python", "AWS"),
        location="Remote",
        experience_level="Senior",
    )

    assert criteria.to_embedding_text() == (
        "Desired role: Backend Engineer | Skills: Python, AWS | "
        "Location: Remote | Experience level: Senior"
    )


def test_prepare_job_normalizes_backend_fields_and_stable_id():
    prepared = prepare_job(
        {
            "job_id": "42",
            "title": "Platform Engineer",
            "company": "Acme",
            "location": "Remote",
            "tags": ["python", "aws"],
            "desc": "Build cloud services.",
            "date_posted": "2026-07-30",
        }
    )

    assert prepared["id"] == "remoteok-42"
    assert prepared["skills"] == ["python", "aws"]
    assert prepared["description"] == "Build cloud services."
    assert prepared["date"] == "2026-07-30"
    assert "Title: Platform Engineer" in prepared["embedding_text"]
    assert "Skills: python, aws" in prepared["embedding_text"]


def test_prepare_job_preserves_existing_source_prefix_and_embedding_text():
    prepared = prepare_job(
        {
            "id": "indeed-7",
            "source": "Indeed",
            "skills": ["sql"],
            "description": "Analyze data.",
            "embedding_text": "custom searchable text",
        }
    )

    assert prepared["id"] == "indeed-7"
    assert prepared["embedding_text"] == "custom searchable text"


def test_prepare_job_requires_an_identifier():
    with pytest.raises(ValueError, match="job_id or id"):
        prepare_job({"title": "Unidentified job"})


def test_service_rejects_non_positive_embedding_batch_size():
    with pytest.raises(ValueError, match="embedding_batch_size"):
        SemanticMatchingService(
            MagicMock(),
            model=MagicMock(),
            embedding_batch_size=0,
        )


def test_index_jobs_is_noop_for_empty_input():
    model = MagicMock()
    store = MagicMock()
    service = SemanticMatchingService(store, model=model)

    service.index_jobs([])

    model.encode.assert_not_called()
    store.upsert_jobs.assert_not_called()


def test_index_jobs_uses_configured_batch_size_and_upserts_vectors():
    model = RecordingModel([[0.1, 0.2], [0.3, 0.4]])
    store = MagicMock()
    service = SemanticMatchingService(
        store,
        model=model,
        embedding_batch_size=2,
    )
    jobs = [
        {"job_id": "1", "title": "Python Engineer"},
        {"job_id": "2", "title": "Data Engineer"},
    ]

    service.index_jobs(jobs)

    texts, options = model.calls[0]
    assert len(texts) == 2
    assert options["batch_size"] == 2
    assert options["normalize_embeddings"] is True
    prepared_jobs, vectors = store.upsert_jobs.call_args.args
    assert [job["id"] for job in prepared_jobs] == [
        "remoteok-1",
        "remoteok-2",
    ]
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_search_filters_results_below_minimum_score():
    model = RecordingModel([[0.5, 0.5]])
    store = MagicMock()
    store.query_jobs.return_value = [
        {"id": "strong", "score": 0.91},
        {"id": "weak", "score": 0.49},
    ]
    service = SemanticMatchingService(
        store,
        model=model,
        minimum_score=0.5,
    )

    results = service.search(
        SearchCriteria(title="Python Engineer"),
        top_k=4,
    )

    assert results == [{"id": "strong", "score": 0.91}]
    store.query_jobs.assert_called_once_with([0.5, 0.5], 4)


def test_search_rejects_empty_criteria_before_encoding():
    model = MagicMock()
    service = SemanticMatchingService(MagicMock(), model=model)

    with pytest.raises(ValueError, match="At least one search field"):
        service.search(SearchCriteria())

    model.encode.assert_not_called()


def test_index_jobs_keeps_stable_id_for_duplicate_job():
    model = RecordingModel([[0.1, 0.2]])
    store = MagicMock()
    service = SemanticMatchingService(store, model=model)
    duplicate_job = {
        "job_id": "123",
        "title": "Python Engineer",
        "company": "Acme",
    }

    service.index_jobs([duplicate_job])
    service.index_jobs([duplicate_job])

    assert store.upsert_jobs.call_count == 2
    first_job = store.upsert_jobs.call_args_list[0].args[0][0]
    second_job = store.upsert_jobs.call_args_list[1].args[0][0]
    assert first_job["id"] == second_job["id"] == "remoteok-123"


def test_search_propagates_error_when_chromadb_is_unavailable():
    model = RecordingModel([[0.5, 0.5]])
    store = MagicMock()
    store.query_jobs.side_effect = RuntimeError("ChromaDB is unavailable")
    service = SemanticMatchingService(store, model=model)

    with pytest.raises(RuntimeError, match="ChromaDB is unavailable"):
        service.search(SearchCriteria(title="Python Engineer"))
