# app/routers/vacancies.py
import httpx
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app import models, schemas
from app.database import get_db
from app.services import hh_service

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


# ------------------- CRUD для вакансий -------------------

@router.get("/", response_model=List[schemas.Vacancy])
def get_vacancies(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список вакансий.
    - status: фильтр по статусу (необязательно)
    - skip: сколько пропустить (для пагинации)
    - limit: максимальное количество записей
    """
    query = db.query(models.Vacancy)
    if status:
        query = query.filter(models.Vacancy.status == status)
    vacancies = query.offset(skip).limit(limit).all()
    return vacancies


@router.get("/{vacancy_id}", response_model=schemas.Vacancy)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """Получить одну вакансию по ID"""
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


@router.post("/", response_model=schemas.Vacancy, status_code=status.HTTP_201_CREATED)
def create_vacancy(vacancy: schemas.VacancyCreate, db: Session = Depends(get_db)):
    """Создать новую вакансию вручную (через тело запроса)"""
    # Проверка на дубликат по URL
    existing = db.query(models.Vacancy).filter(models.Vacancy.url == vacancy.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vacancy with this URL already exists")
    # Создаём запись
    db_vacancy = models.Vacancy(**vacancy.model_dump())
    db.add(db_vacancy)
    db.commit()
    db.refresh(db_vacancy)
    return db_vacancy


class VacancyUpdateStatus(BaseModel):
    status: str

@router.patch("/{vacancy_id}", response_model=schemas.Vacancy)
def update_vacancy_status(vacancy_id: int, update_data: VacancyUpdateStatus, db: Session = Depends(get_db)):
    """Обновить статус вакансии"""
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
    """Удалить вакансию"""
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    db.delete(vacancy)
    db.commit()
    return


# ------------------- Поиск и сохранение с hh.ru -------------------

@router.get("/search", response_model=List[schemas.Vacancy])
async def search_and_save_vacancies(
    query: str,
    area: int = 1,
    db: Session = Depends(get_db)
):
    """
    Ищет вакансии на hh.ru по запросу и региону, сохраняет новые в БД,
    возвращает список сохранённых (только новых) вакансий.
    """
    hh_items = await hh_service.fetch_vacancies_paginated(query, area, pages=2, per_page=20)
    try:
        # Вызываем сервис, передавая per_page=20
        hh_items = await hh_service.fetch_vacancies(query, area, per_page=20)
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching from HH for query '{query}'")
        raise HTTPException(...)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HH.ru API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch from HH: {str(e)}")

    saved_vacancies = []
    for item in hh_items:
        vacancy_data = hh_service.map_hh_vacancy_to_db(item)
        # Проверяем, нет ли уже такой вакансии в БД
        existing = db.query(models.Vacancy).filter(models.Vacancy.url == vacancy_data["url"]).first()
        if existing:
            continue
        new_vacancy = models.Vacancy(**vacancy_data)
        db.add(new_vacancy)
        try:
            db.commit()
            db.refresh(new_vacancy)
            saved_vacancies.append(new_vacancy)
        except IntegrityError:
            db.rollback()
            continue

    return saved_vacancies