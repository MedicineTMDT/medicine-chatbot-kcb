import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import Base

engine = None
AsyncSessionLocal = None

def _setup():
    global engine, AsyncSessionLocal
    if engine is None:
        POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
        engine = create_async_engine(
            POSTGRES_DATABASE_URL,
            pool_size=5,
            max_overflow=0,
            pool_timeout=30,
            pool_recycle=1800,
        )
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

async def init_db():
    _setup()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    _setup()
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
