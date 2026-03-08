from fastapi import FastAPI
from app.routers import vacancies

app = FastAPI(title="HH Vacancy Tracker")

app.include_router(vacancies.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}