import uuid
import pytest

# ==========================================
# TEST CREATE
# ==========================================

@pytest.mark.asyncio
async def test_create_new_conversation(client):
    payload = {"user_id": "user_123", "title": "Chat về AI"}
    response = await client.post("/conversations/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Chat về AI"
    assert data["user_id"] == "user_123"
    assert "id" in data  

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

# ==========================================
# TEST DELETE
# ==========================================

@pytest.mark.asyncio
async def test_delete_conversation_not_found(client):
    random_uuid = str(uuid.uuid4())
    response = await client.delete(f"/conversations/{random_uuid}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found!"}

@pytest.mark.asyncio
async def test_delete_conversation_success(client):
    setup_res = await client.post("/conversations/", json={"user_id": "user_del", "title": "Sẽ bị xóa"})
    conv_id = setup_res.json()["id"]

    response = await client.delete(f"/conversations/{conv_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    get_res = await client.get("/conversations/?user_id=user_del")
    assert len(get_res.json()) == 0

@pytest.mark.asyncio
async def test_delete_conversation_invalid_id_format(client):
    invalid_id = "this-is-not-a-uuid"
    response = await client.delete(f"/conversations/{invalid_id}")

    assert response.status_code == 422

# ==========================================
# TEST GET ALL
# ==========================================

@pytest.mark.asyncio
async def test_get_all_conversations_success(client):
    await client.post("/conversations/", json={"user_id": "user_get", "title": "Hội thoại 1"})
    await client.post("/conversations/", json={"user_id": "user_get", "title": "Hội thoại 2"})

    response = await client.get("/conversations/?user_id=user_get&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_get_all_conversations_empty_list(client):
    response = await client.get("/conversations/?user_id=user_empty&limit=10")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_all_conversations_invalid_query_params(client):
    response = await client.get("/conversations/?user_id=user_123&limit=abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit"]

# ==========================================
# TEST GET ALL
# ==========================================

@pytest.mark.asyncio
async def test_integration_get_messages_success(client):
    conv_payload = {"user_id": "test_user", "title": "Test Chat"}
    conv_res = await client.post("/conversations/", json=conv_payload)
    conv_id = conv_res.json()["id"]

    msg_payload = {"role": "user", "content": "Tin nhắn test"}
    await client.post(f"/conversations/{conv_id}/messages", json=msg_payload)

    response = await client.get(f"/{conv_id}/messages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["conversation_id"] == conv_id
    assert data[0]["content"] == "Tin nhắn test"

@pytest.mark.asyncio
async def test_integration_get_messages_empty(client):
    conv_payload = {"user_id": "test_empty_user", "title": "Empty Chat"}
    conv_res = await client.post("/conversations/", json=conv_payload)
    conv_id = conv_res.json()["id"]

    response = await client.get(f"/{conv_id}/messages")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_integration_get_messages_invalid_uuid(client):
    invalid_id = "12345-abcde"
    
    response = await client.get(f"/{invalid_id}/messages")

    assert response.status_code == 422
    assert "detail" in response.json()

# ==========================================
# TEST UPDATE (PATCH/PUT)
# ==========================================

@pytest.mark.asyncio
async def test_update_conversation_success(client):
    setup_res = await client.post("/conversations/", json={"user_id": "user_upd", "title": "Tên cũ"})
    conv_id = setup_res.json()["id"]

    payload = {"title": "Tên mới đã sửa"} 
    response = await client.patch(f"/conversations/{conv_id}", json=payload)

    assert response.status_code == 200
    assert response.json()["title"] == "Tên mới đã sửa"

@pytest.mark.asyncio
async def test_update_conversation_not_found(client):
    random_uuid = str(uuid.uuid4())
    payload = {"title": "Tên mới"}
    response = await client.patch(f"/conversations/{random_uuid}", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}

@pytest.mark.asyncio
async def test_update_conversation_empty_title(client):
    setup_res = await client.post("/conversations/", json={"user_id": "user_upd", "title": "Tên cũ"})
    conv_id = setup_res.json()["id"]
    
    payload = {"title": ""}
    response = await client.patch(f"/conversations/{conv_id}", json=payload)

    assert response.status_code == 422
