# app/routers/vacancies.py
import httpx
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger   # Добавим логирование для отладки

from app import models, schemas
from app.database import get_db
from app.services import vacancy_service  # <-- Импортируем новый сервис

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


# ===================== ПОИСК И СОХРАНЕНИЕ (НОВЫЙ ЭНДПОИНТ) =====================
@router.get("/search", response_model=List[schemas.Vacancy])
async def search_and_save_vacancies(
    query: str,                     # Поисковый запрос из query-параметра
    db: Session = Depends(get_db)   # Сессия БД через Depends
):
    """
    Ищет вакансии на API Работа России по запросу, сохраняет новые в БД,
    возвращает список сохранённых (только новых) вакансий.
    """
    # 1. Получаем данные от API Работа России
    try:
        # Вызываем функцию из нашего нового vacancy_service
        items = await vacancy_service.fetch_vacancies(query)
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching from Trudvsem for query '{query}'")
        raise HTTPException(status_code=504, detail="API Работа России не отвечает (Timeout)")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Trudvsem: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Ошибка API Работа России: {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Не удалось получить данные: {str(e)}")

    saved_vacancies = []
    # 2. Проходим по каждой полученной вакансии
    for item in items:
        # 2a. Преобразуем данные из формата API в наш внутренний формат
        vacancy_data = vacancy_service.map_vacancy_to_db(item)
        if not vacancy_data.get("url"):
            logger.warning(f"Skipping vacancy without URL: {vacancy_data.get('title')}")
            continue
        
        # 2b. Проверяем, есть ли уже вакансия с таким URL в базе
        existing = db.query(models.Vacancy).filter(models.Vacancy.url == vacancy_data["url"]).first()
        if existing:
            continue    # Если есть, пропускаем
            
        # 2c. Создаём новую запись в БД
        new_vacancy = models.Vacancy(**vacancy_data)
        db.add(new_vacancy)
        
        try:
            db.commit()          # Пытаемся сохранить
            db.refresh(new_vacancy) # Обновляем объект из БД (чтобы получить ID)
            saved_vacancies.append(new_vacancy)
        except IntegrityError:
            # Если произошла ошибка целостности (например, дубликат URL), откатываем транзакцию
            db.rollback()
            logger.warning(f"IntegrityError: Vacancy with URL {vacancy_data['url']} might already exist.")
            continue

    return saved_vacancies


# ===================== ОСТАЛЬНЫЕ ЭНДПОИНТЫ (CRUD) =====================
# Этот эндпоинт возвращает список вакансий из БД (не из API!)
# Он используется для отображения всех сохраненных вакансий на странице "Мои вакансии"
@router.get("/", response_model=List[schemas.Vacancy])
def get_vacancies(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список вакансий из базы данных."""
    query = db.query(models.Vacancy)
    if status:
        query = query.filter(models.Vacancy.status == status)
    vacancies = query.offset(skip).limit(limit).all()
    return vacancies


# ... (все остальные CRUD-эндпоинты для работы с вакансиями: get/{id}, post, patch, delete остаются без изменений)
@router.get("/{vacancy_id}", response_model=schemas.Vacancy)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """Получить одну вакансию по ID."""
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy

@router.post("/", response_model=schemas.Vacancy, status_code=status.HTTP_201_CREATED)
def create_vacancy(vacancy: schemas.VacancyCreate, db: Session = Depends(get_db)):
    """Создать новую вакансию вручную."""
    existing = db.query(models.Vacancy).filter(models.Vacancy.url == vacancy.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vacancy with this URL already exists")
    db_vacancy = models.Vacancy(**vacancy.model_dump())
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    return db_vacancy

class VacancyUpdateStatus(BaseModel):
    status: str

@router.patch("/{vacancy_id}", response_model=schemas.Vacancy)
def update_vacancy_status(vacancy_id: int, update_data: VacancyUpdateStatus, db: Session = Depends(get_db)):
    """Обновить статус вакансии."""
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    vacancy.status = update_data.status
    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)
    return vacancy

@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """Удалить вакансию."""
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    db.delete(vacancy)
    db.commit()
    return