"""Integration tests for FastAPI, semantic matching, and shared ChromaDB."""

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

import python.api as api
from semantic_matching.chroma_store import ChromaJobStore
from semantic_matching.matching_service import SemanticMatchingService


class FakeArray(list):
    """Small ndarray substitute used to keep tests offline and deterministic."""

    def __getitem__(self, index):
        value = super().__getitem__(index)
        return FakeArray(value) if isinstance(value, list) else value

    def tolist(self):
        return [
            item.tolist() if isinstance(item, FakeArray) else item
            for item in self
        ]


class FakeEmbeddingModel:
    def __init__(self):
        self.batch_sizes = []

    def encode(self, texts, **_kwargs):
        self.batch_sizes.append(_kwargs.get("batch_size"))
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([
                float("python" in lowered or "backend" in lowered),
                float("marketing" in lowered),
                0.1,
            ])
        return FakeArray(vectors)


class SemanticIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.model = FakeEmbeddingModel()
        store = ChromaJobStore(
            collection_name="integration_test_jobs",
            path=self.tempdir.name,
            batch_size=1,
        )
        self.service = SemanticMatchingService(
            store,
            minimum_score=0.0,
            model=self.model,
            embedding_batch_size=1,
        )
        self.original_service_factory = api.get_matching_service
        api.get_matching_service = lambda: self.service
        api.index_last_updated = None
        self.client = TestClient(api.app)

    def tearDown(self):
        api.get_matching_service = self.original_service_factory
        self.tempdir.cleanup()

    def test_backend_indexes_and_searches_shared_collection(self):
        jobs = [
            {
                "job_id": "101",
                "title": "Python Backend Engineer",
                "company": "Acme",
                "date_posted": "2026-07-20",
                "location": "Remote",
                "min_salary": "100000",
                "max_salary": "130000",
                "cleaned_salary": "$100,000 - $130,000",
                "apply_url": "https://example.com/101",
                "tags": ["python", "backend"],
                "desc": "Build Python APIs and backend services.",
                "remoteok_url": "https://remoteok.com/remote-jobs/101",
            },
            {
                "job_id": "102",
                "title": "Marketing Coordinator",
                "company": "Beta",
                "date_posted": "2026-07-19",
                "location": "Remote",
                "min_salary": "0",
                "max_salary": "0",
                "apply_url": "https://example.com/102",
                "tags": ["marketing"],
                "desc": "Coordinate marketing campaigns.",
                "remoteok_url": "https://remoteok.com/remote-jobs/102",
            },
        ]

        index_response = self.client.post("/api/jobs", json=jobs)
        self.assertEqual(index_response.status_code, 200)
        self.assertEqual(index_response.json()["count_jobs"], 2)
        self.assertEqual(self.service.store.collection.count(), 2)
        self.assertEqual(self.model.batch_sizes[0], 1)

        search_response = self.client.post(
            "/api/search",
            json={
                "job_title": "Python backend engineer",
                "skills": ["python"],
                "location": "remote",
                "experience_level": "mid",
                "top_n": 2,
            },
        )

        self.assertEqual(search_response.status_code, 200)
        body = search_response.json()
        self.assertEqual(body["match_count"], 2)
        self.assertEqual(body["results"][0]["id"], "remoteok-101")
        self.assertEqual(body["results"][0]["skills"], ["backend", "python"])
        # Salary punctuation can vary with the backend dependency versions
        # used locally and in CI. Verify that the bounds survive the complete
        # FastAPI -> ChromaDB -> search response path.
        normalized_salary = (
            body["results"][0]["salary"]
            .replace("$", "")
            .replace(",", "")
        )
        self.assertEqual(normalized_salary, "100000 - 130000")
        self.assertIsNotNone(body["index_last_updated"])

        route_paths = {route.path for route in api.app.routes}
        self.assertIn("/api/jobs/refresh", route_paths)

    @unittest.skipUnless(
        os.getenv("RUN_REMOTEOK_TEST") == "1",
        "Set RUN_REMOTEOK_TEST=1 to call the real RemoteOK API.",
    )
    def test_live_remoteok_refresh_and_search(self):
        """Verify the live RemoteOK to FastAPI to Chroma workflow."""
        refresh_response = self.client.post(
            "/api/jobs/refresh",
            params={"n": 10},
        )

        self.assertEqual(refresh_response.status_code, 200)
        refresh_body = refresh_response.json()
        self.assertGreater(refresh_body["count_jobs"], 0)
        self.assertGreater(self.service.store.collection.count(), 0)

        search_response = self.client.post(
            "/api/search",
            json={
                "job_title": "software engineer",
                "skills": ["python"],
                "location": "",
                "experience_level": "",
                "top_n": 5,
            },
        )

        self.assertEqual(search_response.status_code, 200)
        search_body = search_response.json()
        self.assertGreater(search_body["match_count"], 0)
        self.assertLessEqual(search_body["match_count"], 5)

        for result in search_body["results"]:
            self.assertIsInstance(result["score"], float)


if __name__ == "__main__":
    unittest.main()
