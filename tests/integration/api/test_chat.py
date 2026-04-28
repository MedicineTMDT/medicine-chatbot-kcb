import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import AIMessage
from langchain_core.documents import Document

from db import crud
from db.postgre.models import Conversation


@pytest.mark.asyncio
@patch("src.services.get_rag_chain")
@patch("src.services.get_llm")
@patch("src.services.get_condense_chain")
async def test_api_e2e_rag_fallback_flow(
    mock_get_condense, 
    mock_get_llm, 
    mock_get_rag, 
    client: AsyncClient, 
    db_session: AsyncSession
):
    valid_uuid = uuid.uuid4()
    payload = {"question": "Paracetamol là thuốc gì?"}

    new_conversation = Conversation(id=valid_uuid) 
    db_session.add(new_conversation)
    await db_session.commit()

    mock_condense = AsyncMock()
    mock_condense.ainvoke.return_value = "Paracetamol là thuốc gì?"
    mock_get_condense.return_value = mock_condense

    mock_llm = MagicMock()
    mock_llm_with_tools = AsyncMock()
    mock_llm_with_tools.ainvoke.return_value = AIMessage(content="", tool_calls=[])
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_get_llm.return_value = mock_llm

    mock_rag = MagicMock()
    async def fake_rag_astream(*args, **kwargs):
        doc = Document(page_content="Giúp hạ sốt.", metadata={"filename": "thuoc.pdf", "page_number": 1})
        yield {"context": [doc]}
        yield {"answer": "Giúp "}
        yield {"answer": "hạ sốt."}
    
    mock_rag.astream = fake_rag_astream
    mock_get_rag.return_value = mock_rag

    response_chunks = []
    async with client.stream("POST", f"/conversations/{valid_uuid}/messages", json=payload) as response:
        assert response.status_code == 200
        async for chunk in response.aiter_text():
            response_chunks.append(chunk)

    full_text = "".join(response_chunks)
    assert "Giúp hạ sốt." in full_text
    
    history = await crud.get_chat_history(db=db_session, conversation_id=valid_uuid, limit=10)
    assert len(history) == 2
    
    ai_msg = history[1]
    assert ai_msg.role == "assistant"
    assert ai_msg.content == "Giúp hạ sốt."
    assert ai_msg.sources is not None
    assert ai_msg.sources[0]["filename"] == "thuoc.pdf"


@pytest.mark.asyncio
@patch.dict("src.tools.AVAILABLE_TOOLS", {"search_drug": AsyncMock(return_value={"uses": "Giảm đau"})})
@patch("src.services.get_llm")
@patch("src.services.get_condense_chain")
async def test_api_e2e_tools_execution_flow(
    mock_get_condense, 
    mock_get_llm, 
    client: AsyncClient, 
    db_session: AsyncSession
):
    valid_uuid = uuid.uuid4()
    payload = {"question": "Tra cứu thuốc Aspirin"}

    new_conversation = Conversation(id=valid_uuid) 
    db_session.add(new_conversation)
    await db_session.commit()

    mock_condense = AsyncMock()
    mock_condense.ainvoke.return_value = "Tra cứu thuốc Aspirin"
    mock_get_condense.return_value = mock_condense

    mock_llm = MagicMock()
    mock_llm_with_tools = AsyncMock()
    
    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{"name": "search_drug", "args": {"name": "Aspirin"}, "id": "call_123"}]
    )
    final_msg = AIMessage(content="", tool_calls=[])
    
    mock_llm_with_tools.ainvoke.side_effect = [tool_call_msg, final_msg]
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    
    async def fake_astream(*args, **kwargs):
        yield MagicMock(content="Aspirin ")
        yield MagicMock(content="giảm đau.")
        
    mock_llm.astream = fake_astream
    mock_get_llm.return_value = mock_llm

    response_chunks = []
    async with client.stream("POST", f"/conversations/{valid_uuid}/messages", json=payload) as response:
        assert response.status_code == 200
        async for chunk in response.aiter_text():
            response_chunks.append(chunk)

    full_text = "".join(response_chunks)
    assert "tool_start" in full_text
    assert "Đang tra cứu chuyên sâu về search_drug" in full_text
    assert "Aspirin" in full_text
    assert "giảm đau." in full_text
    
    history = await crud.get_chat_history(db=db_session, conversation_id=valid_uuid, limit=10)
    assert len(history) == 2
    
    ai_msg = history[1]
    assert ai_msg.role == "assistant"
    assert ai_msg.content == "Aspirin giảm đau."
    
    assert ai_msg.tool_calls is not None
    assert len(ai_msg.tool_calls) == 1
    assert ai_msg.tool_calls[0]["name"] == "search_drug"
    assert ai_msg.tool_calls[0]["args"] == {"name": "Aspirin"}
    assert ai_msg.tool_calls[0]["result"] == {"uses": "Giảm đau"}
