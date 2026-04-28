import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch("api.routes.title.get_llm")
async def test_integration_generate_title_success(mock_get_llm, client):
    create_payload = {"user_id": "test_integration", "title": "Default Title"}
    create_res = await client.post("/conversations/", json=create_payload)
    conv_id = create_res.json()["id"]

    mock_llm_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Hội thoại về Machine Learning"
    mock_llm_instance.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm_instance

    title_payload = {"question": "Machine learning là gì?"}
    response = await client.post(f"/conversations/{conv_id}/title", json=title_payload)

    assert response.status_code == 200
    assert response.json() == "Hội thoại về Machine Learning"

    get_res = await client.get("/conversations/?user_id=test_integration")
    conversations = get_res.json()
    updated_conv = next((c for c in conversations if c["id"] == conv_id), None)
    
    assert updated_conv is not None
    assert updated_conv["title"] == "Hội thoại về Machine Learning"

@pytest.mark.asyncio
@patch("api.routes.title.get_llm")
async def test_integration_generate_title_llm_error_no_db_update(mock_get_llm, client):
    create_payload = {"user_id": "test_integration_err", "title": "Old Title"}
    create_res = await client.post("/conversations/", json=create_payload)
    conv_id = create_res.json()["id"]

    mock_get_llm.side_effect = Exception("OpenAI Error")

    title_payload = {"question": "Lỗi LLM"}
    response = await client.post(f"/conversations/{conv_id}/title", json=title_payload)

    assert response.status_code == 500

    get_res = await client.get("/conversations/?user_id=test_integration_err")
    conversations = get_res.json()
    unchanged_conv = next((c for c in conversations if c["id"] == conv_id), None)

    assert unchanged_conv is not None
    assert unchanged_conv["title"] == "Old Title"

@pytest.mark.asyncio
async def test_integration_generate_title_invalid_uuid(client):
    title_payload = {"question": "Câu hỏi test"}
    response = await client.post("/conversations/invalid-id-format/title", json=title_payload)

    assert response.status_code == 422
