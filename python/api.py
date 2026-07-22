import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from api_description_cleaning import clean_description
from api_salary_extraction import extract_salary_bounds
import re
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
    location: str = ""
    experience_level: str = ""
    top_n: int = Field(default=20, ge=1, le=100)


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
            min_salary=None,
            max_salary=None,
            cleaned_salary=None,
            apply_url=str(raw_job.get("apply_url", "")),
            job_id=f"remoteok:{raw_job.get('id')}",
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


def to_frontend_job(job: JobListing) -> FrontendJob:
    return FrontendJob(
        id=job.job_id,
        score=None,
        title=job.title,
        company=job.company or None,
        location=job.location or None,
        salary=job.cleaned_salary,
        role_type=None,
        date_listed=job.date_posted or None,
        description=job.desc,
        skills=job.tags,
        apply_url=job.apply_url or job.remoteok_url,
    )


@app.post("/api/search", response_model=SearchResponse,)
def search_jobs(request: SearchRequest) -> SearchResponse:
    query_tags = ",".join(request.skills)

    jobs = fetch_job_postings(query_tags=query_tags, position=request.job_title,)

    # apply location filtering locally
    if request.location and request.location.casefold() != "remote":
        requested_location = request.location.casefold()

        jobs = [job for job in jobs if requested_location in job.location.casefold()]

    selected_jobs = jobs[:request.top_n]

    frontend_jobs = [to_frontend_job(job) for job in selected_jobs]

    skill_counts: dict[str, int] = {}

    for job in selected_jobs:
        for skill in job.tags:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    skill_frequency = [
        {
            "skill": skill,
            "count": count,
        }
        for skill, count in sorted(
            skill_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return SearchResponse(
        query_echo=request,
        match_count=len(frontend_jobs),
        results=frontend_jobs,
        analytics={
            "skill_frequency": skill_frequency,
        },
    )


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
    job.min_salary, job.max_salary = extract_salary_bounds(job.desc)
    job.cleaned_salary = combine_salary_bounds(job.min_salary, job.max_salary,)

    return job


@app.post("/api/jobs")
def post_jobs(jobs: list[JobListing]):
    return {"status": "Success", "count_jobs": len(jobs), "received_jobs": jobs}
