"""Normalize RemoteOK job records and build text suitable for embeddings."""

from __future__ import annotations

import argparse
import html
import json
import re
from typing import Any


TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_html(value: Any) -> str:
    """Convert HTML-heavy API text into compact plain text."""
    text = html.unescape(str(value or ""))
    text = TAG_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip()


def normalize_job(job: dict[str, Any]) -> dict[str, Any]:
    """Return the consistent job format expected by the matching pipeline."""
    tags = [clean_html(tag).lower() for tag in job.get("tags", []) if tag]
    normalized = {
        "id": str(job.get("id", "")),
        "title": clean_html(job.get("position")),
        "company": clean_html(job.get("company")),
        "location": clean_html(job.get("location")) or "Remote",
        "description": clean_html(job.get("description")),
        "skills": sorted(set(tags)),
        "salary_min": int(job.get("salary_min") or 0),
        "salary_max": int(job.get("salary_max") or 0),
        "apply_url": job.get("apply_url") or job.get("url") or "",
        "date": job.get("date") or "",
        "source": "Remote OK",
    }

    normalized["embedding_text"] = " | ".join(
        part
        for part in [
            f"Title: {normalized['title']}",
            f"Company: {normalized['company']}",
            f"Location: {normalized['location']}",
            f"Skills: {', '.join(normalized['skills'])}",
            f"Description: {normalized['description']}",
        ]
        if part.split(": ", 1)[-1]
    )
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="remoteok_jobs_raw.json")
    parser.add_argument("--output", default="remoteok_jobs_normalized.json")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as file:
        raw_jobs = json.load(file)

    normalized_jobs = [normalize_job(job) for job in raw_jobs]
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(normalized_jobs, file, indent=2, ensure_ascii=False)

    print(f"Normalized {len(normalized_jobs)} jobs into {args.output}")


if __name__ == "__main__":
    main()
