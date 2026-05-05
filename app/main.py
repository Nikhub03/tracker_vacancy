# app/main.py
from fastapi import FastAPI
# Импортируем наш роутер из папки routers
from app.routers import vacancies

app = FastAPI(title="HH Vacancy Tracker")

# Подключаем роутер вакансий.
# FastAPI "включит" все маршруты из vacancies.router в наше главное приложение.
app.include_router(vacancies.router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}