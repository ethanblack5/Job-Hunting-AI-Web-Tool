import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
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

    job_dict = {}

    search_params = {
        "tags": query_tags,
        "position": position,
        "date": date
    }

    response = requests.get(url, params=search_params, headers=headers, timeout=10)
    job_json = response.json()

    for index, job in enumerate(job_json):

        new_job = JobListing(title=job["position"],
                             company=job["company"],
                             date_posted=job["date"],
                             location=job["location"],
                             min_salary=job["salary_min"],
                             max_salary=job["salary_max"],
                             apply_url=job["apply_url"],
                             job_id=job["id"],
                             tags=job["tags"],
                             desc=job["description"],
                             remoteok_url=job["url"])
        processed_job = process_job(new_job)
        dict_var = f"job_{index}"
        job_dict[dict_var] = processed_job

    return job_dict


def process_job(job: JobListing) -> JobListing:
    """
    Normalizes data for one job under the JobListing object.
    """

    # standardize to only include YYYY-MM-DD format
    job.date_posted = job.date_posted[0:10]

    # standardize job location to only include relevant parts
    # without extraneous trailing characters
    for index, char in enumerate(job.location):
        if char == ',' and index + 2 == len(job.location):
            stop_index = index
            job.location = job.location[0:stop_index + 1]
            break

    if job.min_salary == 0:
        job.min_salary = None

    if job.max_salary == 0:
        job.max_salary = None

    return job

@app.get("/api/posts")
def get_jobs():
    return


if __name__ == "__main__":
    get_job_postings("Accountant", "Accountant", "2026-07-12")
