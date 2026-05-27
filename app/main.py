from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import vacancies

# 1. Сначала создаём приложение
app = FastAPI(title="HH Vacancy Tracker")

# 2. Теперь можно монтировать статику (если папка существует)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# 3. Добавляем CORS (разрешаем запросы с любых источников на время разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Подключаем роутеры
app.include_router(vacancies.router)

# 5. Эндпоинты
@app.get("/")
def root():
    return {"message": "Welcome to HH Vacancy Tracker"}

@app.get("/health")
def health():
    return {"status": "ok"}
