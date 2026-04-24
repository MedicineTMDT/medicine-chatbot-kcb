import pytest
import json
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from api.main import app
from db import get_db

class FakeCondenseChain:
    async def ainvoke(self, inputs):
        return "câu hỏi độc lập đã được xử lý"

class FakeRAGChain:
    async def astream(self, inputs):
        mock_doc = MagicMock()
        mock_doc.page_content = "Thông tin y tế về đau đầu."
        mock_doc.metadata = {"filename": "sach_y_khoa.pdf", "page_number": 15}
        yield {"context": [mock_doc]}
        
        yield {"answer": "Bạn "}
        yield {"answer": "nên "}
        yield {"answer": "uống nhiều nước."}

class FakeLLMWithTools:
    async def ainvoke(self, messages):
        mock_ai_msg = MagicMock()
        mock_ai_msg.tool_calls = [] 
        return mock_ai_msg

class FakeLLM:
    def bind_tools(self, tools):
        return FakeLLMWithTools()

async def override_get_db():
    yield "mocked_db_session"

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
TEST_UUID = str(uuid.uuid4())

API_FILE_PATH = "api.routers.chat"  

@patch(f"{API_FILE_PATH}.get_condense_chain")
@patch(f"{API_FILE_PATH}.get_rag_chain")
@patch(f"{API_FILE_PATH}.get_llm")
@patch("db.crud.get_chat_history", new_callable=AsyncMock)
@patch("db.crud.save_message", new_callable=AsyncMock)
@patch(f"{API_FILE_PATH}.BASE_URL_FILE", "https://my-mock-storage.com/")
def test_ask_question_stream_rag_fallback(
    mock_save_message,
    mock_get_history,
    mock_get_llm,
    mock_get_rag,
    mock_get_condense
):
    # 1. Chuẩn bị Mock Data
    mock_get_history.return_value = [] # Không có lịch sử chat
    
    # Gắn các class giả lập vào các hàm get_chain
    mock_get_condense.return_value = FakeCondenseChain()
    mock_get_rag.return_value = FakeRAGChain()
    mock_get_llm.return_value = FakeLLM()

    # 2. Gọi API
    payload = {"question": "Tôi bị đau đầu thì làm sao?"}
    
    # Ghi chú: TestClient sẽ tự động chờ stream kết thúc và gom lại thành response.text
    response = client.post(f"/conversations/{TEST_UUID}/messages", json=payload)

    # 3. Kiểm tra kết quả
    assert response.status_code == 200
    
    # Bóc tách nội dung stream trả về
    response_text = response.text
    
    # Kiểm tra xem có đúng chuẩn Server-Sent Events không
    assert response_text.startswith("data: ")
    
    # Kiểm tra chunk "start"
    assert '"type":"start"' in response_text
    
    # Kiểm tra các chunk "stream" có chứa câu trả lời từ FakeRAGChain không
    assert "Bạn " in response_text
    assert "nên " in response_text
    assert "uống nhiều nước." in response_text
    
    # Kiểm tra chunk "end" có source link chuẩn xác không
    assert '"type":"end"' in response_text
    assert "sach_y_khoa.pdf#page=15" in response_text

    # 4. Kiểm tra xem các hàm DB có được gọi đúng không
    # Hàm lưu câu hỏi của user (gọi trước khi stream)
    mock_save_message.assert_any_call(
        db="mocked_db_session",
        conversation_id=uuid.UUID(TEST_UUID),
        role="user",
        content="Tôi bị đau đầu thì làm sao?"
    )
    
    # Hàm lưu câu trả lời của AI (gọi sau khi stream xong)
    # Lấy ra lời gọi hàm cuối cùng để kiểm tra
    last_save_call_kwargs = mock_save_message.call_args_list[-1].kwargs
    assert last_save_call_kwargs["role"] == "assistant"
    assert last_save_call_kwargs["content"] == "Bạn nên uống nhiều nước."
    assert last_save_call_kwargs["sources"][0]["filename"] == "sach_y_khoa.pdf"
