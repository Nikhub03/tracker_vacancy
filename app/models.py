# app/models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

# Класс `Vacancy` наследуется от `Base`. Это означает, что SQLAlchemy знает, что на его основе нужно создать таблицу в БД.
class Vacancy(Base):
    # `__tablename__` - это имя таблицы в базе данных. Оно может отличаться от имени класса.
    __tablename__ = "vacancies"

    # column - это колонка в таблице. Первый аргумент (int, str) - это тип данных в Python.
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        # Это необязательный метод, но он полезен для отладки. Он определяет, как объект будет выглядеть в консоли.
        return f"<Vacancy {self.title}>"