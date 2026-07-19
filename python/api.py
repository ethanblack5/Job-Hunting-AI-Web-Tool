import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from api_description_cleaning import clean_description
# pip install requests fastapi[standard] pydantic typing

app = FastAPI()
url = "https://www.remoteok.com/api"
titles = []

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
    min_salary: Optional[int]
    max_salary: Optional[int]
    apply_url: str
    job_id: str
    tags: list
    desc: str
    remoteok_url: str


@app.get("/job-batch/")
def get_job_postings(query_tags: str, position: str, date: str):
    """
    API returns json keys 'slug', 'id', 'epoch', 'date', 'company',
    'company_logo', 'position', 'tags', 'description', 'location',
    'apply_url', 'salary_min', 'salary_max', 'logo', and 'url' per job posting
    """

    jobs = []

    search_params = {
        "tags": query_tags,
        "position": position,
        "date": date
    }

    try:
        response = requests.get(url, params=search_params, headers=headers, timeout=10)
        response.raise_for_status()
        job_json = response.json()

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

        new_job = JobListing(
                            title=job.get("position", ""),
                             company=job.get("company", ""),
                             date_posted=job.get("date", ""),
                             location=job.get("location", ""),
                             min_salary=job.get("salary_min", ""),
                             max_salary=job.get("salary_max", ""),
                             apply_url=job.get("apply_url", ""),
                             job_id=job.get("id", ""),
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
    for index, char in enumerate(job.location):
        if char == ',' and index + 2 == len(job.location):
            stop_index = index
            job.location = job.location[:stop_index + 1]
            break

    if job.min_salary == 0:
        job.min_salary = None

    if job.max_salary == 0:
        job.max_salary = None

    job.desc = clean_description(job.desc)

    return job

@app.post("/api/jobs")
def post_jobs(jobs: JobListing):
    return {"status": "Success", "received_jobs": jobs}
