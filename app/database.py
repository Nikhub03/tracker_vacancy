from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Обращение к БД или ее создание если ее не существует
SQLALCHEMY_DATABASE_URL = "sqlite:///./hh_tracker.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Автоматическое управление сессиями FastAPI,
# где каждый новый запрос к серверу создает новую сессию, потом после обработки запроса ее закрывает
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
