# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Для MVP мы будем использовать простую и удобную SQLite
# Файл базы данных 'hh_tracker.db' автоматически создастся в корневой папке проекта
SQLALCHEMY_DATABASE_URL = "sqlite:///./hh_tracker.db"

# `engine` - это "двигатель", который будет физически подключаться к нашей базе данных
# `connect_args={"check_same_thread": False}` - специальный параметр, необходимый для SQLite,
# который разрешает доступ к базе данных из разных потоков. В реальном проекте с PostgreSQL он не нужен.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# `SessionLocal` - это "фабрика" по созданию сессий.
# Сессия - это конкретное подключение к базе данных, через которое мы будем выполнять операции.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `Base` - это фундамент для всех наших моделей (таблиц).
# Мы будем наследовать наши классы таблиц от этого класса.
Base = declarative_base()

# Эта функция нужна для того, чтобы FastAPI мог автоматически управлять жизненным циклом сессии.
# Каждый новый запрос к серверу будет создавать новую сессию, а после обработки запроса - закрывать её.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()