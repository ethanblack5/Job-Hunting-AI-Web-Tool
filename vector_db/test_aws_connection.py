"""Optional connectivity test for a remotely hosted Chroma server."""

import os

import chromadb
import pytest


@pytest.mark.skipif(
    not os.getenv("CHROMA_AWS_HOST"),
    reason="Set CHROMA_AWS_HOST to run the remote Chroma integration test.",
)
def test_aws_chroma_connection():
    """Verify that an explicitly configured remote Chroma server responds."""
    client = chromadb.HttpClient(
        host=os.environ["CHROMA_AWS_HOST"],
        port=int(os.getenv("CHROMA_AWS_PORT", "8000")),
    )

    assert client.heartbeat() > 0
