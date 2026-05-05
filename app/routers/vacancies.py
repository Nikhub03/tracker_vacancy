# app/routers/vacancies.py
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Импортируем наши собственные модули
from app import models, schemas
from app.database import get_db

# Создаём экземпляр роутера. Префикс "/vacancies" означает, что все пути здесь будут начинаться с этого.
# Тэг "vacancies" нужен для группировки в документации Swagger.
router = APIRouter(prefix="/vacancies", tags=["vacancies"])


# --- GET: Получить список всех вакансий ---
# `response_model` — говорит FastAPI, какую схему использовать для форматирования ответа.
# List[schemas.Vacancy] означает, что вернётся список объектов, соответствующих схеме Vacancy.
@router.get("/", response_model=List[schemas.Vacancy])
def get_vacancies(db: Session = Depends(get_db)):
    """
    Возвращает список всех вакансий из базы данных.
    """
    # db.query(models.Vacancy) — это SQL-запрос "SELECT * FROM vacancies"
    # .all() выполняет запрос и возвращает все найденные записи.
    vacancies = db.query(models.Vacancy).all()
    return vacancies


# --- GET: Получить одну вакансию по ID ---
@router.get("/{vacancy_id}", response_model=schemas.Vacancy)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """
    Возвращает одну вакансию по её ID. Если не найдено, возвращает ошибку 404.
    """
    # .filter() добавляет условие "WHERE id = vacancy_id"
    # .first() выполняет запрос и возвращает первую запись, или None, если ничего не найдено.
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        # HTTPException позволяет вернуть код ошибки и понятное сообщение
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


# --- POST: Создать новую вакансию ---
# `response_model` указывает, что в случае успеха нужно вернуть схему Vacancy.
# `status_code=201` — означает, что ресурс успешно создан.
@router.post("/", response_model=schemas.Vacancy, status_code=status.HTTP_201_CREATED)
def create_vacancy(vacancy: schemas.VacancyCreate, db: Session = Depends(get_db)):
    """
    Создаёт новую вакансию в базе данных.
    """
    # Проверяем, нет ли уже вакансии с таким URL
    existing_vacancy = db.query(models.Vacancy).filter(models.Vacancy.url == vacancy.url).first()
    if existing_vacancy:
        raise HTTPException(status_code=400, detail="Vacancy with this URL already exists")

    # Создаём объект нашей SQLAlchemy-модели, передавая в него данные из Pydantic-схемы.
    # **vacancy.dict() — распаковывает словарь с полями в аргументы функции.
    db_vacancy = models.Vacancy(**vacancy.model_dump())
    # Добавляем объект в сессию. Это как сказать "я готовлю эту запись к добавлению".
    db.add(db_vacancy)
    # Сохраняем все изменения, накопленные в сессии, в базу данных.
    db.commit()
    # Обновляем наш объект из базы данных, чтобы он получил сгенерированные поля (например, id и created_at).
    db.refresh(db_vacancy)
    return db_vacancy


# --- PATCH: Обновить статус вакансии ---
# Эта схема нужна только для обновления статуса. Мы можем определить её прямо здесь.
class VacancyUpdateStatus(BaseModel):
    status: str

@router.patch("/{vacancy_id}", response_model=schemas.Vacancy)
def update_vacancy_status(vacancy_id: int, update_data: VacancyUpdateStatus, db: Session = Depends(get_db)):
    """
    Обновляет статус существующей вакансии.
    """
    # Сначала находим вакансию, как в GET-запросе по ID
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    
    # Обновляем поле статуса новым значением из тела запроса
    vacancy.status = update_data.status
    # Добавляем изменённый объект в сессию (SQLAlchemy и сам его отслеживает, но явно добавить не помешает)
    db.add(vacancy)
    # Сохраняем изменения
    db.commit()
    # Обновляем объект, чтобы он был в актуальном состоянии
    db.refresh(vacancy)
    return vacancy


# --- DELETE: Удалить вакансию ---
@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """
    Удаляет вакансию из базы данных.
    """
    # Находим вакансию
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    
    # Удаляем объект из сессии, а значит и из базы данных
    db.delete(vacancy)
    # Сохраняем изменения
    db.commit()
    # При статусе 204 No Content мы не возвращаем никакого тела ответа, поэтому здесь просто return.
    return