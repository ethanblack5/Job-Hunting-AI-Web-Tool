"""Fetch a small, normalized sample of jobs from the RemoteOK public API."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests

REMOTEOK_API_URL = "https://remoteok.com/api"
HEADERS = {
    "User-Agent": "CS467-JobHunter/0.1 (student project; source: Remote OK)"
}


def fetch_remoteok_jobs(limit: int = 25, timeout: int = 20) -> list[dict[str, Any]]:
    """Fetch RemoteOK jobs, excluding the API metadata record."""
    response = requests.get(REMOTEOK_API_URL, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("RemoteOK returned an unexpected response format.")

    jobs = [item for item in payload if isinstance(item, dict) and item.get("id")]
    return jobs[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--output", default="remoteok_jobs_raw.json")
    args = parser.parse_args()

    jobs = fetch_remoteok_jobs(limit=args.limit)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(jobs)} RemoteOK jobs to {args.output}")


if __name__ == "__main__":
    main()
