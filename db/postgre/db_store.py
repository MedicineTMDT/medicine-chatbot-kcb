from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

from .models import Base

engine = create_engine(
    POSTGRES_DATABASE_URL,
    pool_size=5,
    max_overflow=0,
    pool_timeout=30,
    pool_recycle=1800,
)

def init_db():
    Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()