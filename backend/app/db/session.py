from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

_initialized = False

def ensure_initialized():
    global _initialized
    if not _initialized:
        try:
            from app.db.init_db import init_db
            init_db()
            _initialized = True
        except Exception:
            pass

def get_db():
    ensure_initialized()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
