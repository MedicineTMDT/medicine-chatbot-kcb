import pytest
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from unittest.mock import AsyncMock, MagicMock, patch
from db import crud

@pytest.mark.asyncio
async def test_integration_stream_rag_fallback_with_fixture(chat_handler, db_session):
    handler, conversation_id = chat_handler
    
    handler.condense_chain.ainvoke.return_value = "Tác dụng của Paracetamol là gì?"
    handler.mock_llm_with_tools.ainvoke.return_value = AIMessage(content="", tool_calls=[])

    async def mock_rag_astream(*args, **kwargs):
        doc = Document(page_content="Paracetamol giúp hạ sốt.", metadata={"filename": "thuoc.pdf", "page_number": 1})
        yield {"context": [doc]}
        yield {"answer": "Paracetamol "}
        yield {"answer": "giúp hạ sốt."}

    handler.rag_chain.astream = mock_rag_astream

    events = []
    async for event in handler.stream_generator():
        events.append(event)

    import pprint
    pprint.pprint(events)

    assert len(events) == 4
    assert "start" in events[0]
    assert "Paracetamol " in events[1]
    assert "giúp hạ sốt." in events[2]
    assert "end" in events[3]
    
    history = await crud.get_chat_history(db=db_session, conversation_id=conversation_id, limit=10)
    
    assert len(history) == 2, "Phải lưu đủ 1 câu hỏi user và 1 câu trả lời AI"
    
    user_msg = history[0]
    assert user_msg.role == "user"
    assert user_msg.content == "Tác dụng của Paracetamol là gì?"
    
    ai_msg = history[1]
    assert ai_msg.role == "assistant"
    assert ai_msg.content == "Paracetamol giúp hạ sốt."
    assert ai_msg.sources is not None
    assert ai_msg.sources[0]["filename"] == "thuoc.pdf"


@pytest.mark.asyncio
async def test_integration_stream_tool_calling_with_fixture(chat_handler, db_session):
    handler, conversation_id = chat_handler

    handler.condense_chain.ainvoke.return_value = "Tác dụng của Paracetamol là gì?"
    
    tool_call_message = AIMessage(
        content="",
        tool_calls=[{"name": "search_drug", "args": {"name": "Paracetamol"}, "id": "call_123"}]
    )
    final_message = AIMessage(content="", tool_calls=[])
    
    handler.mock_llm_with_tools.ainvoke.side_effect = [tool_call_message, final_message]

    async def mock_llm_astream(*args, **kwargs):
        yield MagicMock(content="Theo kết quả, ")
        yield MagicMock(content="thuốc giúp hạ sốt.")
        
    handler.llm.astream = mock_llm_astream

    mock_tool_func = AsyncMock()
    mock_tool_func.return_value = {"name": "Paracetamol", "uses": "Hạ sốt, giảm đau"}

    with patch.dict("src.tools.AVAILABLE_TOOLS", {"search_drug": mock_tool_func}):
        
        events = []
        async for event in handler.stream_generator():
            events.append(event)

    assert len(events) == 5
    assert "start" in events[0]
    assert "tool_start" in events[1] 
    assert "search_drug" in events[1] 
    assert "Theo kết quả, " in events[2]
    assert "thuốc giúp hạ sốt." in events[3]
    assert "end" in events[4]
    
    mock_tool_func.assert_called_once_with(name="Paracetamol")
    assert handler.tool_was_called is True

    history = await crud.get_chat_history(db=db_session, conversation_id=conversation_id, limit=10)
    
    assert len(history) == 2
    
    ai_msg = history[1]
    assert ai_msg.role == "assistant"
    assert ai_msg.content == "Theo kết quả, thuốc giúp hạ sốt."
    
    assert ai_msg.tool_calls is not None, "Trường tool_calls trong DB không được để trống"
    assert len(ai_msg.tool_calls) == 1
    
    saved_tool_call = ai_msg.tool_calls[0]
    assert saved_tool_call["name"] == "search_drug"
    assert saved_tool_call["args"] == {"name": "Paracetamol"}
    assert saved_tool_call["result"] == {"name": "Paracetamol", "uses": "Hạ sốt, giảm đau"}
