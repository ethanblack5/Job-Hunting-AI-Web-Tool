import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from api_description_cleaning import clean_description
import re
# pip install requests fastapi[standard] pydantic

app = FastAPI()
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
    min_salary: int
    max_salary: int
    apply_url: str
    job_id: str
    tags: list[str] = Field(default_factory=list)
    desc: str
    remoteok_url: str


@app.get("/job-batch/", response_model=list[JobListing])
def get_job_postings(query_tags: str, position: str, date: str):
    """
    API returns json keys 'slug', 'id', 'epoch', 'date', 'company',
    'company_logo', 'position', 'tags', 'description', 'location',
    'apply_url', 'salary_min', 'salary_max', 'logo', and 'url' per job posting
    """

    jobs: list[JobListing] = []

    search_params = {
        "tags": query_tags,
        "position": position,
        "date": date
    }

    try:
        response = requests.get(url, params=search_params, headers=headers, timeout=10)
        response.raise_for_status()
        job_json = response.json()

        if not isinstance(job_json, list):
            raise HTTPException(
                status_code=502,
                detail="Unexpected response format."
            )

    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail="RemoteOK request timed out."
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

    for job in job_json:
        if not isinstance(job, dict):
            continue

        if not job.get("id") or not job.get("position"):
            continue

        new_job = JobListing(
                            title=job.get("position", ""),
                            company=job.get("company", ""),
                            date_posted=job.get("date", ""),
                            location=job.get("location", ""),
                            min_salary=job.get("salary_min", ""),
                            max_salary=job.get("salary_max", ""),
                            apply_url=job.get("apply_url", ""),
                            job_id=str(job.get("id", "")),
                            tags=job.get("tags", []),
                            desc=job.get("description", ""),
                            remoteok_url=job.get("url", "")
                            )

        processed_job = process_job(new_job)
        jobs.append(processed_job)

    return jobs


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

    if job.min_salary == 0:
        job.min_salary = None

    if job.max_salary == 0:
        job.max_salary = None

    job.desc = clean_description(job.desc)

    return job


@app.post("/api/jobs")
def post_jobs(jobs: list[JobListing]):
    return {"status": "Success", "count_jobs": len(jobs), "received_jobs": jobs}
