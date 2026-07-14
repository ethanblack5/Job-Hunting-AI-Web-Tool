"""
JobPilot AI — ChromaDB regression and unit tests
Owner: Chloe Vo

Covers schema validation and Chroma ops behavior, including:
- record conversion
- idempotent batch insert
- similarity search with filters
- get-by-id lookup
- delete operations
- required metadata enforcement
- pydantic backend compatibility
"""

import random
import tempfile
import unittest
from typing import Any, Dict, List

from pydantic import BaseModel

from chroma_ops import (
    add_posting,
    add_postings_batch,
    count,
    delete_posting,
    get_by_id,
    job_listing_to_chroma_record,
    similarity_search,
)
from chroma_schema import get_client, get_or_create_collection, REQUIRED_METADATA_FIELDS
from sample_remoteok_jobs import RAW_SAMPLE_JOBS

EMBED_DIM = 384


def fake_embedding(seed_text: str) -> List[float]:
    random.seed(hash(seed_text) % (2**32))
    return [random.uniform(-1, 1) for _ in range(EMBED_DIM)]


def make_sample_job(job_id: str, **overrides: Any) -> Dict[str, Any]:
    job = {
        "job_id": job_id,
        "title": "Healthcare Support Specialist",
        "company": "Acme Health",
        "tags": ["medical", "support", "communication"],
        "location": "Remote",
        "apply_url": "https://remoteok.com/remote-jobs/1",
        "remoteok_url": "https://remoteok.com/remote-jobs/1",
        "date_posted": "2026-07-13",
        "min_salary": None,
        "max_salary": None,
        "desc": "Provide patient support, coordinate intake, and improve communication.",
    }
    job.update(overrides)
    return job


class FakeJobListing(BaseModel):
    job_id: str
    title: str
    company: str
    tags: List[str]
    location: str
    apply_url: str
    remoteok_url: str
    date_posted: str
    min_salary: int
    max_salary: int
    desc: str


def reset_sample_records(collection) -> None:
    sample_ids = [job["job_id"] for job in RAW_SAMPLE_JOBS]
    collection.delete(ids=sample_ids)


def build_records(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        job_listing_to_chroma_record(job, embedding=fake_embedding(job["desc"]), source="remoteok")
        for job in jobs
    ]


def test_chroma_pipeline() -> None:
    client = get_client()
    collection = get_or_create_collection(client)

    reset_sample_records(collection)
    starting_count = count(collection)

    records = build_records(RAW_SAMPLE_JOBS)
    add_postings_batch(collection, records)

    assert count(collection) == starting_count + len(records)

    query_vec = fake_embedding("healthcare medical patient communication support")
    results = similarity_search(collection, query_vec, n_results=3)
    assert len(results["ids"][0]) == 3
    assert len(results["metadatas"][0]) == 3

    filtered = similarity_search(collection, query_vec, n_results=5, source="remoteok")
    assert all(item["source"] == "remoteok" for item in filtered["metadatas"][0])

    sample_id = RAW_SAMPLE_JOBS[0]["job_id"]
    retrieved = get_by_id(collection, sample_id)
    assert retrieved["ids"][0] == sample_id
    assert retrieved["metadatas"][0]["title"] == RAW_SAMPLE_JOBS[0]["title"]

    pydantic_job = FakeJobListing(**RAW_SAMPLE_JOBS[0])
    pydantic_record = job_listing_to_chroma_record(
        pydantic_job,
        embedding=[0.1] * EMBED_DIM,
        source="remoteok",
    )
    assert pydantic_record["metadata"]["min_salary"] == 0
    assert pydantic_record["metadata"]["max_salary"] == 0
    assert pydantic_record["metadata"]["remoteok_url"] == RAW_SAMPLE_JOBS[0]["remoteok_url"]


class ChromaOpsSchemaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.client = get_client(path=self.tempdir.name)
        self.collection = get_or_create_collection(self.client)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_get_or_create_collection_returns_collection(self) -> None:
        self.assertIsNotNone(self.collection)
        self.assertEqual(self.collection.name, "job_postings")

    def test_job_listing_to_chroma_record_converts_values(self) -> None:
        raw_job = make_sample_job("123", tags=["patient", "remote"], min_salary=None, max_salary=None)
        record = job_listing_to_chroma_record(raw_job, embedding=fake_embedding("123"), source="remoteok")

        self.assertEqual(record["source_id"], "123")
        self.assertEqual(record["metadata"]["tags"], "patient,remote")
        self.assertEqual(record["metadata"]["min_salary"], 0)
        self.assertEqual(record["metadata"]["max_salary"], 0)
        self.assertEqual(record["metadata"]["source"], "remoteok")
        self.assertEqual(record["document"], raw_job["desc"])

    def test_job_listing_to_chroma_record_accepts_pydantic_model(self) -> None:
        raw_job = make_sample_job("124", min_salary=50000, max_salary=60000)
        pydantic_job = FakeJobListing(**raw_job)

        record = job_listing_to_chroma_record(
            pydantic_job,
            embedding=fake_embedding("124"),
            source="remoteok",
        )

        self.assertEqual(record["metadata"]["min_salary"], 50000)
        self.assertEqual(record["metadata"]["max_salary"], 60000)
        self.assertEqual(record["source_id"], "124")

    def test_add_posting_and_get_by_id(self) -> None:
        record = job_listing_to_chroma_record(
            make_sample_job("201"),
            embedding=fake_embedding("201"),
            source="remoteok",
        )

        add_posting(
            self.collection,
            record["source_id"],
            record["embedding"],
            record["document"],
            record["metadata"],
        )

        self.assertEqual(count(self.collection), 1)

        retrieved = get_by_id(self.collection, record["source_id"])
        self.assertEqual(retrieved["ids"][0], record["source_id"])
        self.assertEqual(retrieved["metadatas"][0]["title"], record["metadata"]["title"])

    def test_add_postings_batch_and_count(self) -> None:
        records = [
            job_listing_to_chroma_record(
                make_sample_job(str(i), desc=f"Job description {i}"),
                embedding=fake_embedding(str(i)),
                source="remoteok",
            )
            for i in range(3)
        ]

        add_postings_batch(self.collection, records)
        self.assertEqual(count(self.collection), 3)

    def test_similarity_search_applies_filters(self) -> None:
        records = [
            job_listing_to_chroma_record(
                make_sample_job("301", title="Remote Nurse", desc="nurse patient care", location="Remote"),
                embedding=fake_embedding("nurse"),
                source="remoteok",
            ),
            job_listing_to_chroma_record(
                make_sample_job("302", title="Software Engineer", desc="python backend developer", location="San Francisco"),
                embedding=fake_embedding("developer"),
                source="remoteok",
            ),
            job_listing_to_chroma_record(
                make_sample_job("303", title="Customer Support", desc="phone and email support", location="Remote"),
                embedding=fake_embedding("support"),
                source="indeed",
            ),
        ]

        add_postings_batch(self.collection, records)

        results = similarity_search(
            self.collection,
            fake_embedding("medical support"),
            n_results=2,
            source="remoteok",
        )

        self.assertEqual(len(results["ids"][0]), 2)
        self.assertTrue(all(metadata["source"] == "remoteok" for metadata in results["metadatas"][0]))

        filtered_by_location = similarity_search(
            self.collection,
            fake_embedding("medical support"),
            n_results=3,
            location="Remote",
        )

        self.assertTrue(all(metadata["location"] == "Remote" for metadata in filtered_by_location["metadatas"][0]))

    def test_delete_posting_removes_record(self) -> None:
        record = job_listing_to_chroma_record(
            make_sample_job("401"),
            embedding=fake_embedding("401"),
            source="remoteok",
        )

        add_posting(
            self.collection,
            record["source_id"],
            record["embedding"],
            record["document"],
            record["metadata"],
        )
        self.assertEqual(count(self.collection), 1)

        delete_posting(self.collection, record["source_id"])
        self.assertEqual(count(self.collection), 0)

    def test_add_posting_rejects_missing_required_metadata(self) -> None:
        incomplete_metadata = {field: "value" for field in REQUIRED_METADATA_FIELDS if field != "company"}

        with self.assertRaises(ValueError):
            add_posting(self.collection, "500", [0.0] * EMBED_DIM, "document", incomplete_metadata)

    def test_add_postings_batch_rejects_missing_required_metadata(self) -> None:
        bad_record = {
            "source_id": "501",
            "embedding": [0.0] * EMBED_DIM,
            "document": "document",
            "metadata": {"title": "Missing fields"},
        }

        with self.assertRaises(ValueError):
            add_postings_batch(self.collection, [bad_record])


if __name__ == "__main__":
    unittest.main()
