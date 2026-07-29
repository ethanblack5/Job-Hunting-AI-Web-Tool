from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()


@app.get("/api/search")
async def receive_search_params(
    job_title: Optional[str] = Query(None, min_length=2),
    skills: Optional[list[str]] = Query(None),
    location: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    limit: int = Query(20, le=50),
):
    # Process your data here
    return {
        "job_title": job_title,
        "skills": skills,
        "location": location,
        "experience_level": experience_level,
        "top_n": limit
    }
