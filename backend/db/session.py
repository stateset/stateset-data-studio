from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.settings import settings

# ---------------------------------------------------------------------------
# Database URL & engine
# ---------------------------------------------------------------------------
DATABASE_URL = settings.database_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
