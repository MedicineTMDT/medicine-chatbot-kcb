from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

engine = create_engine(POSTGRES_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()