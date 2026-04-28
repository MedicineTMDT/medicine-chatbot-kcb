import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
@patch("api.routes.title.crud.update_conversation_title", new_callable=AsyncMock)
@patch("api.routes.title.build_title_prompt")
@patch("api.routes.title.get_llm")
async def test_generate_title_success(mock_get_llm, mock_build_prompt, mock_update_title, client):
    mock_llm_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "  Hội thoại về AI  "
    mock_llm_instance.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm_instance

    mock_prompt_template = MagicMock()
    mock_prompt_template.format.return_value = "Đây là câu hỏi: AI là gì?"
    mock_build_prompt.return_value = mock_prompt_template

    mock_update_title.return_value = True

    conv_id = str(uuid.uuid4())
    payload = {"question": "AI là gì?"}

    response = await client.post(f"/conversations/{conv_id}/title", json=payload)

    assert response.status_code == 200
    assert response.json() == "Hội thoại về AI"

    mock_get_llm.assert_called_once_with(temperature=0.1, is_chat_model=False)
    mock_prompt_template.format.assert_called_once_with(question="AI là gì?")
    mock_llm_instance.invoke.assert_called_once_with("Đây là câu hỏi: AI là gì?")
    mock_update_title.assert_called_once()
    
    kwargs = mock_update_title.call_args.kwargs
    assert str(kwargs["conversation_id"]) == conv_id
    assert kwargs["title"] == "Hội thoại về AI"

@pytest.mark.asyncio
@patch("api.routes.title.get_llm")
async def test_generate_title_server_error(mock_get_llm, client):
    mock_get_llm.side_effect = Exception("LLM Connection Failed")

    conv_id = str(uuid.uuid4())
    payload = {"question": "AI là gì?"}

    response = await client.post(f"/conversations/{conv_id}/title", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "LLM Connection Failed"

@pytest.mark.asyncio
async def test_generate_title_invalid_uuid(client):
    payload = {"question": "AI là gì?"}
    
    response = await client.post("/conversations/invalid-uuid-string/title", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "conversation_id"]

@pytest.mark.asyncio
async def test_generate_title_missing_payload(client):
    conv_id = str(uuid.uuid4())
    
    response = await client.post(f"/conversations/{conv_id}/title", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "question"]
