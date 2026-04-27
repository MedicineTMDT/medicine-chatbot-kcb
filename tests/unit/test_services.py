import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
@patch("db.crud.save_message", new_callable=AsyncMock)
@patch("db.crud.get_chat_history", new_callable=AsyncMock)
async def test_stream_generator_rag_fallback(mock_get_history, mock_save_msg, chat_handler):
    mock_get_history.return_value = []
    
    chat_handler.condense_chain.ainvoke.return_value = "Paracetamol có tác dụng gì?"
    chat_handler.mock_llm_with_tools.ainvoke.return_value = AIMessage(content="", tool_calls=[])

    async def mock_rag_astream(*args, **kwargs):
        doc_mock = MagicMock(page_content="Nội dung tài liệu", metadata={"filename": "thuoc.pdf", "page_number": 1})
        yield {"context": [doc_mock]}
        yield {"answer": "Paracetamol "}
        yield {"answer": "giúp hạ sốt."}

    chat_handler.rag_chain.astream = mock_rag_astream

    events = []
    async for event in chat_handler.stream_generator():
        events.append(event)

    assert len(events) == 4
    assert "start" in events[0]
    assert "Paracetamol " in events[1]
    assert "giúp hạ sốt." in events[2]
    assert "end" in events[3]
    
    assert mock_get_history.call_count == 1
    assert mock_save_msg.call_count == 2


# ==========================================
# TOOL
# ==========================================

@pytest.mark.asyncio
@patch("db.crud.save_message", new_callable=AsyncMock)
@patch("db.crud.get_chat_history", new_callable=AsyncMock)
async def test_stream_generator_with_tool_calls(mock_get_history, mock_save_msg, chat_handler):
    mock_get_history.return_value = []
    
    mock_tool_func = AsyncMock()
    mock_tool_func.return_value = {"name": "Paracetamol", "uses": "Hạ sốt, giảm đau"}
    
    with patch.dict("src.tools.AVAILABLE_TOOLS", {"search_drug": mock_tool_func}):
        
        tool_call_message = AIMessage(
            content="",
            tool_calls=[{"name": "search_drug", "args": {"name": "Paracetamol"}, "id": "call_123"}]
        )
        final_message = AIMessage(content="", tool_calls=[])
        
        chat_handler.mock_llm_with_tools.ainvoke.side_effect = [tool_call_message, final_message]

        async def mock_llm_astream(*args, **kwargs):
            yield MagicMock(content="Theo kết quả, ")
            yield MagicMock(content="thuốc giúp hạ sốt.")
            
        chat_handler.llm.astream = mock_llm_astream

        events = []
        async for event in chat_handler.stream_generator():
            events.append(event)

        assert len(events) == 5
        assert "start" in events[0]
        assert "tool_start" in events[1] 
        assert "search_drug" in events[1] 
        assert "Theo kết quả, " in events[2]
        assert "thuốc giúp hạ sốt." in events[3]
        assert "end" in events[4]
        
        mock_tool_func.assert_called_once_with(name="Paracetamol")
        assert chat_handler.tool_was_called is True
