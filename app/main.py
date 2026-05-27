from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import vacancies

# Создание приложения
app = FastAPI(title="HH Vacancy Tracker")

# Монтировка статики
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Добавление CORS (разрешаем запросы с любых источников на время разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(vacancies.router)

# Эндпоинты
@app.get("/")
def root():
    return {"message": "Welcome to Vacancy Tracker"}

@app.get("/health")
def health():
    return {"status": "ok"}
