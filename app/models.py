from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vacancy {self.title}>"