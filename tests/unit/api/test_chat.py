import pytest
import uuid
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch("api.routes.chat.ChatStreamHandler")
async def test_ask_question_stream_success(mock_handler_class, client):
    mock_instance = MagicMock()
    
    async def fake_stream():
        yield 'data: {"type": "start"}\n\n'
        yield 'data: {"type": "stream", "answer": "Hello"}\n\n'
        
    mock_instance.stream_generator.return_value = fake_stream()
    mock_handler_class.return_value = mock_instance

    valid_uuid = str(uuid.uuid4())
    payload = {"question": "Chào bạn"}

    response = await client.post(f"/conversations/{valid_uuid}/messages", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8" 
    
    response_text = response.text
    assert 'data: {"type": "start"}' in response_text
    assert 'data: {"type": "stream", "answer": "Hello"}' in response_text

    mock_handler_class.assert_called_once()
    kwargs = mock_handler_class.call_args.kwargs
    assert str(kwargs["conversation_id"]) == valid_uuid
    assert kwargs["question"] == "Chào bạn"

@pytest.mark.asyncio
async def test_ask_question_stream_invalid_uuid(client):
    payload = {"question": "Chào bạn"}
    response = await client.post("/conversations/invalid-uuid-string/messages", json=payload)

    assert response.status_code == 422

@pytest.mark.asyncio
@patch("api.routes.chat.ChatStreamHandler")
async def test_ask_question_stream_server_error(mock_handler_class, client):
    mock_handler_class.side_effect = Exception("Database connection lost")

    valid_uuid = str(uuid.uuid4())
    payload = {"question": "Chào bạn"}

    response = await client.post(f"/conversations/{valid_uuid}/messages", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "Database connection lost"
