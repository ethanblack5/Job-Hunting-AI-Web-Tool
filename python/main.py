from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
import httpx

app = FastAPI()


@app.get("/fetch-external-data")
async def get_remoteok_data():

    url = "https://remoteok.com/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"External server error: {exc}"
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to external server: {exc}"
            )
