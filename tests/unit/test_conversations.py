import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import uuid

from api.main import app 
from db import get_db

async def override_get_db():
    yield "mocked_db_session"

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

TEST_UUID = str(uuid.uuid4())


@patch("db.crud.create_conversation", new_callable=AsyncMock)
def test_create_new_conversation(mock_create):
    mock_create.return_value = {
        "id": TEST_UUID,
        "user_id": "user_123",
        "title": "Chat về AI"
    }

    payload = {"user_id": "user_123", "title": "Chat về AI"}
    response = client.post("/conversations/", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Chat về AI"
    assert response.json()["user_id"] == "user_123"
    
    mock_create.assert_called_once()



@patch("db.crud.get_conversations_by_user", new_callable=AsyncMock)
def test_get_all_conversations(mock_get_all):
    mock_get_all.return_value = [
        {"id": TEST_UUID, "user_id": "user_123", "title": "Cuộc hội thoại 1"}
    ]

    response = client.get("/conversations/?user_id=user_123&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Cuộc hội thoại 1"


@patch("db.crud.delete_conversation", new_callable=AsyncMock)
def test_delete_conversation_not_found(mock_delete):
    mock_delete.return_value = False

    response = client.delete(f"/conversations/{TEST_UUID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found!"}


@patch("db.crud.delete_conversation", new_callable=AsyncMock)
def test_delete_conversation_success(mock_delete):
    mock_delete.return_value = True

    response = client.delete(f"/conversations/{TEST_UUID}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "successfully" in response.json()["message"]


@patch("db.crud.update_conversation_title", new_callable=AsyncMock)
def test_update_conversation_manual(mock_update):
    class MockConv:
        id = TEST_UUID
        title = "Tên mới đã sửa"
        
    mock_update.return_value = MockConv()

    payload = {"title": "  Tên mới đã sửa  "} 
    response = client.patch(f"/conversations/{TEST_UUID}", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Tên mới đã sửa"
