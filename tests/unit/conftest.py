import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from src.services import ChatStreamHandler

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from api.main import app 
from db.postgre.db_store import get_db 

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest_asyncio.fixture
async def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
def conversation_id():
    return uuid.uuid4()

@pytest.fixture
def chat_handler(mock_db, conversation_id):
    handler = ChatStreamHandler(
        db=mock_db, 
        conversation_id=conversation_id, 
        question="Tác dụng của Paracetamol là gì?"
    )
    
    handler.condense_chain = MagicMock()
    handler.condense_chain.ainvoke = AsyncMock()
    
    handler.llm = MagicMock()
    handler.mock_llm_with_tools = MagicMock()
    handler.mock_llm_with_tools.ainvoke = AsyncMock()

    handler.llm.bind_tools = MagicMock(return_value=handler.mock_llm_with_tools)
    handler.rag_chain = MagicMock()
    
    return handler
