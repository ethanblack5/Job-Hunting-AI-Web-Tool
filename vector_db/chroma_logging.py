"""
Lightweight logging to visualize what's happening in Chroma
during testing:

1. How big is the index right now (how many postings are indexed)
2. How many queries are we running, and how fast are they
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("chroma_monitor")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(Path(__file__).with_name("chroma_metrics.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Keeps track of how many queries we've run, grouped by hour.
_query_counts: dict = defaultdict(int)


def log_index_size(collection) -> int:
    """
    Logs how many records are currently in the collection.
    Returns the count.
    """
    size = collection.count()
    logger.info(f"Index size for '{collection.name}': {size} postings")
    return size


def _current_hour_bucket() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00 UTC")


def log_query(
    collection,
    n_results: int,
    elapsed_seconds: float,
    source: Optional[str] = None,
    location: Optional[str] = None,
) -> None:
    """
    Logs one query against the collection, including how many results were returned,
    how long it took, and any metadata filters that were applied.
    Also increments the in-memory query count for this hour.
    """
    _query_counts[_current_hour_bucket()] += 1

    filters_used = []
    if source:
        filters_used.append(f"source={source}")
    if location:
        filters_used.append(f"location={location}")
    filter_note = f", filters: {', '.join(filters_used)}" if filters_used else ""

    logger.info(
        f"Query on '{collection.name}' returned {n_results} results "
        f"in {elapsed_seconds * 1000:.1f}ms{filter_note}"
    )


def timed_similarity_search(
    collection,
    query_embedding: list,
    n_results: int = 5,
    location: Optional[str] = None,
    source: Optional[str] = None,
):
    """
    Wraps similarity_search() to time the query and log it.
    Returns the same results as similarity_search().
    """
    from chroma_ops import similarity_search

    start = time.perf_counter()
    results = similarity_search(
        collection,
        query_embedding,
        n_results=n_results,
        location=location,
        source=source,
        log_query_activity=False,
    )
    elapsed = time.perf_counter() - start

    log_query(
        collection,
        len(results.get("ids", [[]])[0]),
        elapsed,
        source=source,
        location=location,
    )
    return results


def report_query_volume() -> None:
    """
    Prints a quick summary of how many queries were run, broken down
    by hour.
    """
    if not _query_counts:
        logger.info("No queries recorded yet this session.")
        return

    logger.info("Query volume this session:")
    for hour, query_count in sorted(_query_counts.items()):
        logger.info(f"  {hour}: {query_count} quer{'y' if query_count == 1 else 'ies'}")
