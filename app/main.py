# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import vacancies
from fastapi.staticfiles import StaticFiles
import os

# Если папка static существует, раздаём из неё файлы
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app = FastAPI(title="HH Vacancy Tracker")

# Разрешаем запросы с любых источников (на время разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vacancies.router)

@app.get("/")
def root():
    return {"message": "Welcome to HH Vacancy Tracker"}

@app.get("/health")
def health():
    return {"status": "ok"}