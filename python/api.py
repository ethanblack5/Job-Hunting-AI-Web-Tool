import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
url = "https://remoteok.com/api"
titles = []


class JobListing(BaseModel):
    title: str
    company: str
    date_posted: str
    location: str
    min_salary: int
    max_salary: int
    apply_url: str
    job_id: str
    tags: list
    desc: str

@app.get("/postings")
def get_job_postings(query_tags: str, position: str, date: str):
    
    search_params = {
        "tags":query_tags,
        "position": position,
        "date": date
    }
    response = requests.get(url, params=search_params)
    job_json = response.json()
    add_jobs(job_json)

@app.post("/postings")
async def add_jobs(api_json):

    job_dict = {}

    for index, job in enumerate(api_json):

        var_name = f"job_{index}"
        job_dict[var_name] = {
            # complete later
        }

@app.get("/job-titles")
def get_titles():
    return titles
