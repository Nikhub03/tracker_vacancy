# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Базовая схема. Содержит общие для всех операции поля.
class VacancyBase(BaseModel):
    title: str
    company: str
    url: str

# Схема для создания новой вакансии (POST-запрос)
class VacancyCreate(VacancyBase):
    status: Optional[str] = "new"

# Схема, которую мы будем отдавать клиенту (GET-запрос)
# Наследуется от VacancyBase и добавляет поля, которые приходят из базы данных.
class Vacancy(VacancyBase):
    id: int
    status: str
    created_at: datetime

    # Этот вложенный класс говорит Pydantic, как преобразовать данные из SQLAlchemy-модели в нашу схему.
    class Config:
        from_attributes = True