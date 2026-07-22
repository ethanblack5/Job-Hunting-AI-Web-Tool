"""
Tests the retrieval layer end-to-end: index some fake postings,
embed a query, and confirm ranked results + the API response shape
come back correctly.
"""

import tempfile
import unittest

from chroma_schema import get_client, get_or_create_collection
from chroma_ops import add_posting
from retrieval import retrieve, retrieve_for_api, embed_query


def sample_metadata(**overrides):
    metadata = {
        "title": "Backend Engineer",
        "company": "Acme Corp",
        "date_posted": "2026-07-01",
        "location": "Remote",
        "min_salary": 90000,
        "max_salary": 120000,
        "apply_url": "https://example.com/apply/1",
        "tags": "python,backend",
        "remoteok_url": "https://remoteok.com/remote-jobs/1",
        "source": "remoteok",
    }
    metadata.update(overrides)
    return metadata


class RetrievalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.client = get_client(path=self.tempdir.name)
        self.collection = get_or_create_collection(self.client)

        # Index a couple of postings using REAL embeddings, so the
        # query embedding is comparable to them (same model, same space).
        add_posting(
            self.collection, "1",
            embed_query("backend python developer job"),
            "Backend engineering role working with Python and APIs.",
            sample_metadata(title="Backend Engineer"),
        )
        add_posting(
            self.collection, "2",
            embed_query("marketing coordinator social media"),
            "Coordinate marketing campaigns and social media presence.",
            sample_metadata(title="Marketing Coordinator", company="Beta Inc"),
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_retrieve_ranks_relevant_result_first(self) -> None:
        results = retrieve(self.collection, "python backend job", top_n=2)

        self.assertEqual(len(results), 2)
        # the backend posting should score higher than the marketing one
        self.assertEqual(results[0]["metadata"]["title"], "Backend Engineer")
        self.assertGreater(results[0]["similarity_score"], results[1]["similarity_score"])

    def test_retrieve_for_api_shape(self) -> None:
        response = retrieve_for_api(self.collection, "python backend job", top_n=2)

        self.assertIn("query", response)
        self.assertIn("results", response)
        self.assertIn("count", response)
        self.assertEqual(response["count"], 2)

        first_result = response["results"][0]
        self.assertIn("job_id", first_result)
        self.assertIn("similarity_score", first_result)


if __name__ == "__main__":
    unittest.main()
