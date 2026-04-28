import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from api.main import app 
from db import get_db
from db.postgre.models import Base, Conversation
from src.services import ChatStreamHandler

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest_asyncio.fixture(scope="function")
async def async_engine(postgres_container):
    raw_url = postgres_container.get_connection_url()
    db_url = raw_url.replace("psycopg2", "asyncpg").replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with TestingSessionLocal() as session:
        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

@pytest.fixture
async def chat_handler(db_session):
    conversation_id = uuid.uuid4()
    question = "Tác dụng của Paracetamol là gì?"

    new_conversation = Conversation(id=conversation_id) 
    db_session.add(new_conversation)
    await db_session.commit()
    
    handler = ChatStreamHandler(
        db=db_session, 
        conversation_id=conversation_id, 
        question=question
    )
    
    handler.condense_chain = MagicMock()
    handler.condense_chain.ainvoke = AsyncMock()
    
    handler.llm = MagicMock()
    handler.mock_llm_with_tools = MagicMock()
    handler.mock_llm_with_tools.ainvoke = AsyncMock()

    handler.llm.bind_tools = MagicMock(return_value=handler.mock_llm_with_tools)
    handler.rag_chain = MagicMock()
    
    return handler, conversation_id
