import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import re

from .api_description_cleaning import clean_description
from .api_salary_extraction import extract_salary_bounds
from semantic_matching.chroma_store import ChromaJobStore
from semantic_matching.matching_service import (
    SearchCriteria,
    SemanticMatchingService,
)
# pip install requests fastapi[standard] pydantic

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Create React App
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

url = "https://www.remoteok.com/api"
index_last_updated: datetime | None = None

headers = {
    "User-Agent": "Job-Hunting-AI-Web-Tool/1.0"
}


class JobListing(BaseModel):
    """
    Job object used per listing from RemoteOK API data
    """
    title: str
    company: str
    date_posted: str
    location: str

    min_salary: str | None = None
    max_salary: str | None = None
    cleaned_salary: str | None = None

    apply_url: str
    job_id: str
    tags: list[str] = Field(default_factory=list)
    desc: str
    remoteok_url: str


class SearchRequest(BaseModel):
    job_title: str = ""
    skills: list[str] = Field(default_factory=list)
    location: str = "remote"
    experience_level: str = ""
    top_n: int = Field(default=20, ge=1, le=50)


@lru_cache(maxsize=1)
def get_matching_service() -> SemanticMatchingService:
    """Load the embedding model and shared Chroma collection once."""
    return SemanticMatchingService(ChromaJobStore())


class FrontendJob(BaseModel):
    id: str
    score: float | None = None
    title: str
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    role_type: str | None = None
    date_listed: str | None = None
    description: str
    skills: list[str] = Field(default_factory=list)
    apply_url: str


class SearchResponse(BaseModel):
    query_echo: SearchRequest
    match_count: int
    index_last_updated: str | None = None
    results: list[FrontendJob]
    analytics: dict


def fetch_job_postings(
    query_tags: str = "",
    position: str = "",
    date: str = "",
) -> list[JobListing]:
    jobs: list[JobListing] = []

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        job_json = response.json()

        if not isinstance(job_json, list):
            raise HTTPException(
                status_code=502,
                detail="Unexpected response format.",
            )

    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Remote OK request timed out.",
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Remote OK request failed: {exc}",
        ) from exc

    except requests.exceptions.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Remote OK returned invalid JSON.",
        ) from exc

    requested_tags = {
        tag.strip().casefold()
        for tag in query_tags.split(",")
        if tag.strip()
    }

    for raw_job in job_json:
        if not isinstance(raw_job, dict):
            continue

        if not all([
            raw_job.get("id"),
            raw_job.get("position"),
            raw_job.get("description"),
        ]):
            continue

        raw_title = str(raw_job.get("position", ""))
        raw_date = str(raw_job.get("date", ""))
        raw_tags = raw_job.get("tags", [])

        if not isinstance(raw_tags, list):
            raw_tags = []

        normalized_tags = {
            str(tag).strip().casefold()
            for tag in raw_tags
            if str(tag).strip()
        }

        if (position and position.casefold() not in raw_title.casefold()):
            continue

        if (requested_tags and not requested_tags.intersection(normalized_tags)):
            continue

        if date and not raw_date.startswith(date):
            continue

        new_job = JobListing(
            title=raw_title,
            company=str(raw_job.get("company", "")),
            date_posted=raw_date,
            location=str(raw_job.get("location", "")),
            min_salary=str(raw_job.get("salary_min", 0)),
            max_salary=str(raw_job.get("salary_max", 0)),
            cleaned_salary=None,
            apply_url=str(raw_job.get("apply_url", "")),
            job_id=f"remoteok-{raw_job.get('id')}",
            tags=raw_tags,
            desc=str(raw_job.get("description", "")),
            remoteok_url=str(raw_job.get("url", "")),
        )

        jobs.append(process_job(new_job))

    return jobs


@app.get("/job-batch/", response_model=list[JobListing],)
def get_job_postings(
    query_tags: str = "",
    position: str = "",
    date: str = "",
    n: int = Query(default=20, ge=1, le=100),
):
    jobs = fetch_job_postings(
        query_tags=query_tags,
        position=position,
        date=date,
    )
    return jobs[:n]


def combine_salary_bounds(
    minimum: str | None,
    maximum: str | None,
) -> str | None:
    if minimum is None:
        return None

    if maximum is None or minimum == maximum:
        return minimum

    return f"{minimum} - {maximum}"


def process_job(job: JobListing) -> JobListing:
    """
    Normalizes data for one job under the JobListing object.
    """

    # standardize to only include YYYY-MM-DD format
    job.date_posted = job.date_posted[:10]

    # standardize job location to only include relevant parts
    # without extraneous trailing characters
    job.location = re.sub(r"\s+", " ", job.location).strip(" ,")

    job.tags = sorted({
        str(tag).strip().casefold()
        for tag in job.tags
        if str(tag).strip()
    })

    job.desc = clean_description(job.desc)

    extracted_min = None
    extracted_max = None

    if job.min_salary == "0" or job.max_salary == "0":
        extracted_min, extracted_max = extract_salary_bounds(job.desc)

    if job.min_salary == "0":
        job.min_salary = extracted_min

    if job.max_salary == "0":
        job.max_salary = extracted_max

    job.cleaned_salary = combine_salary_bounds(
        job.min_salary,
        job.max_salary,
    )

    return job


@app.post("/api/jobs")
def post_jobs(jobs: list[JobListing]):
    """Embed and upsert normalized backend jobs into shared ChromaDB."""
    processed_jobs = [process_job(job.model_copy(deep=True)) for job in jobs]
    return index_jobs(processed_jobs)


def index_jobs(jobs: list[JobListing]) -> dict:
    """Index already-normalized jobs and record the refresh time."""
    global index_last_updated
    get_matching_service().index_jobs(jobs)
    index_last_updated = datetime.now(timezone.utc)
    return {
        "status": "Success",
        "count_jobs": len(jobs),
        "index_last_updated": index_last_updated.isoformat(),
    }


@app.post("/api/jobs/refresh")
def refresh_jobs(
    query_tags: str = "",
    position: str = "",
    date: str = "",
    n: int = Query(default=20, ge=1, le=100),
):
    """Fetch RemoteOK jobs, normalize them, and refresh the shared index."""
    jobs = fetch_job_postings(
        query_tags=query_tags,
        position=position,
        date=date,
    )[:n]
    return index_jobs(jobs)


@app.post("/api/search", response_model=SearchResponse)
def search_jobs(request: SearchRequest) -> SearchResponse:
    """Run semantic search against jobs indexed through /api/jobs."""
    if not (
        request.job_title.strip()
        or request.skills
        or request.location.strip()
        or request.experience_level.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one search field is required.",
        )

    criteria = SearchCriteria(
        title=request.job_title.strip(),
        skills=tuple(skill.strip() for skill in request.skills if skill.strip()),
        location=request.location.strip(),
        experience_level=request.experience_level.strip(),
    )

    try:
        service = get_matching_service()
        if service.store.collection.count() == 0:
            index_jobs(fetch_job_postings())
        results = service.search(criteria, top_k=request.top_n)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Semantic search is unavailable: {exc}",
        ) from exc

    skill_counts = Counter(
        skill
        for result in results
        for skill in result.get("skills", [])
    )
    return SearchResponse(
        query_echo=request,
        match_count=len(results),
        index_last_updated=(
            index_last_updated.isoformat() if index_last_updated else None
        ),
        results=results,
        analytics={
            "skill_frequency": [
                {"skill": skill, "count": count}
                for skill, count in skill_counts.most_common(10)
            ]
        },
    )
