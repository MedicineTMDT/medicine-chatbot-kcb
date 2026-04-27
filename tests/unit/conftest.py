import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock # Nhớ import thêm MagicMock

from src.services import ChatStreamHandler

@pytest.fixture
def mock_db():
    return AsyncMock()

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
