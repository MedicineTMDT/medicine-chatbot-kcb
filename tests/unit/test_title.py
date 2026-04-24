import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from api.main import app
from db import get_db

async def override_get_db():
    yield "mocked_db_session"

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
TEST_UUID = str(uuid.uuid4())


API_FILE_PATH = "api.routers.title"

@patch(f"{API_FILE_PATH}.get_llm")
@patch("db.crud.update_conversation_title", new_callable=AsyncMock)
def test_generate_title_success(mock_update_title, mock_get_llm):
    mock_ai_response = MagicMock()
    mock_ai_response.content = "   Tư vấn về đau đầu   " 

    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = mock_ai_response
    mock_get_llm.return_value = mock_llm_instance

    mock_update_title.return_value = True

    payload = {"question": "Tôi bị đau đầu và buồn nôn thì phải làm sao?"}
    response = client.post(f"/conversations/{TEST_UUID}/title", json=payload)

    assert response.status_code == 200
    
    assert response.json() == "Tư vấn về đau đầu"

    mock_get_llm.assert_called_once_with(temperature=0.1, model_name="gpt-4o-mini")
    
    mock_update_title.assert_called_once_with(
        db="mocked_db_session",
        conversation_id=uuid.UUID(TEST_UUID),
        title="Tư vấn về đau đầu" 
    )
