import uuid
import pytest
from unittest.mock import patch, AsyncMock
from db.postgre.models import Conversation
from datetime import datetime, timezone

@pytest.mark.asyncio
@patch("db.postgre.crud.create_conversation", new_callable=AsyncMock)
async def test_create_new_conversation(mock_create, client):
    mock_create.return_value = {
        "id": str(uuid.uuid4()),
        "user_id": "user_123",
        "title": "Chat về AI"
    }
    payload = {"user_id": "user_123", "title": "Chat về AI"}
    response = await client.post("/conversations/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Chat về AI"
    assert data["user_id"] == "user_123"
    assert "id" in data
    mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_create_conversation_missing_required_field(client):
    payload = {"title": "Chat về AI"}
    response = await client.post("/conversations/", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "user_id"]

@pytest.mark.asyncio
async def test_create_conversation_invalid_data_type(client):
    payload = {"user_id": ["user_123"], "title": "Chat về AI"}
    response = await client.post("/conversations/", json=payload)

    assert response.status_code == 422

@pytest.mark.asyncio
@patch("db.postgre.crud.delete_conversation", new_callable=AsyncMock)
async def test_delete_conversation_not_found(mock_delete, client):
    mock_delete.return_value = None
    random_uuid = str(uuid.uuid4())
    response = await client.delete(f"/conversations/{random_uuid}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found!"}
    mock_delete.assert_called_once()

@pytest.mark.asyncio
@patch("db.postgre.crud.delete_conversation", new_callable=AsyncMock)
async def test_delete_conversation_success(mock_delete, client):
    mock_delete.return_value = True
    conv_id = str(uuid.uuid4())
    response = await client.delete(f"/conversations/{conv_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_delete.assert_called_once()

@pytest.mark.asyncio
async def test_delete_conversation_invalid_id_format(client):
    invalid_id = "this-is-not-a-uuid"
    response = await client.delete(f"/conversations/{invalid_id}")

    assert response.status_code == 422

@pytest.mark.asyncio
@patch("db.postgre.crud.get_conversations_by_user", new_callable=AsyncMock)
async def test_get_all_conversations_success(mock_get_all, client):
    mock_get_all.return_value = [
        {"id": str(uuid.uuid4()), "user_id": "user_get", "title": "Hội thoại 1"},
        {"id": str(uuid.uuid4()), "user_id": "user_get", "title": "Hội thoại 2"}
    ]
    response = await client.get("/conversations/?user_id=user_get&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_get_all.assert_called_once()

@pytest.mark.asyncio
@patch("db.postgre.crud.get_conversations_by_user", new_callable=AsyncMock)
async def test_get_all_conversations_empty_list(mock_get_all, client):
    mock_get_all.return_value = []
    response = await client.get("/conversations/?user_id=user_empty&limit=10")

    assert response.status_code == 200
    assert response.json() == []
    mock_get_all.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_conversations_invalid_query_params(client):
    response = await client.get("/conversations/?user_id=user_123&limit=abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit"]

@pytest.mark.asyncio
@patch("db.postgre.crud.get_chat_history", new_callable=AsyncMock)
async def test_unit_get_messages_success(mock_get_chat_history, client):
    conv_id = str(uuid.uuid4())
    mock_get_chat_history.return_value = [
        {
            "id": str(uuid.uuid4()), 
            "conversation_id": conv_id, 
            "role": "user", 
            "content": "Hello AI",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()), 
            "conversation_id": conv_id, 
            "role": "assistant", 
            "content": "Chào bạn!",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    response = await client.get(f"/conversations/{conv_id}/messages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Hello AI"
    mock_get_chat_history.assert_called_once()

@pytest.mark.asyncio
@patch("db.postgre.crud.get_chat_history", new_callable=AsyncMock)
async def test_unit_get_messages_empty(mock_get_chat_history, client):
    conv_id = str(uuid.uuid4())
    mock_get_chat_history.return_value = []
    
    response = await client.get(f"/conversations/{conv_id}/messages")

    assert response.status_code == 200
    assert response.json() == []
    mock_get_chat_history.assert_called_once()

@pytest.mark.asyncio
async def test_unit_get_messages_invalid_uuid(client):
    invalid_id = "not-a-valid-uuid"
    
    response = await client.get(f"/conversations/{invalid_id}/messages")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "conversation_id"]

@pytest.mark.asyncio
@patch("db.postgre.crud.update_conversation_title", new_callable=AsyncMock)
async def test_update_conversation_success(mock_update, client):
    conv_id = str(uuid.uuid4())
    mock_update.return_value = Conversation(id=conv_id, user_id="user_upd",title="Tên mới đã sửa")
    payload = {"title": "Tên mới đã sửa"} 
    response = await client.patch(f"/conversations/{conv_id}", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Tên mới đã sửa"
    mock_update.assert_called_once()

@pytest.mark.asyncio
@patch("db.postgre.crud.update_conversation_title", new_callable=AsyncMock)
async def test_update_conversation_not_found(mock_update, client):
    mock_update.return_value = None
    random_uuid = str(uuid.uuid4())
    payload = {"title": "Tên mới"}
    response = await client.patch(f"/conversations/{random_uuid}", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}
    mock_update.assert_called_once()

@pytest.mark.asyncio
async def test_update_conversation_empty_title(client):
    conv_id = str(uuid.uuid4())
    payload = {"title": ""}
    response = await client.patch(f"/conversations/{conv_id}", json=payload)

    assert response.status_code == 422
