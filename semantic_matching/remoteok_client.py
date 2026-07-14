"""Fetch a small, normalized sample of jobs from the RemoteOK public API."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


REMOTEOK_API_URL = "https://remoteok.com/api"

HEADERS = {
    "User-Agent": (
        "CS467-JobHunter/0.1 "
        "(student project; source: Remote OK)"
    )
}


def fetch_remoteok_jobs(
    limit: int = 25,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Fetch RemoteOK jobs while excluding the API metadata record."""
    response = requests.get(
        REMOTEOK_API_URL,
        headers=HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError(
            "RemoteOK returned an unexpected response format."
        )

    jobs = [
        item
        for item in payload
        if isinstance(item, dict) and item.get("id")
    ]

    return jobs[:limit]


def save_jobs(
    jobs: list[dict[str, Any]],
    output_path: str,
) -> None:
    """Save fetched jobs to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            jobs,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    """Run the RemoteOK job-fetching script."""
    parser = argparse.ArgumentParser(
        description="Fetch job postings from the RemoteOK API."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of jobs to fetch.",
    )

    parser.add_argument(
        "--output",
        default="remoteok_jobs_raw.json",
        help="Path for the output JSON file.",
    )

    args = parser.parse_args()

    try:
        jobs = fetch_remoteok_jobs(limit=args.limit)
        save_jobs(jobs, args.output)

        print(
            f"Saved {len(jobs)} RemoteOK jobs "
            f"to {args.output}"
        )

    except requests.RequestException as error:
        print(f"RemoteOK API request failed: {error}")
        raise SystemExit(1) from error

    except (ValueError, json.JSONDecodeError) as error:
        print(f"Unable to process RemoteOK response: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
