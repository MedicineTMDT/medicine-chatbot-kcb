import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from api.schemas.completion import CompletionResponse

@pytest.mark.asyncio
@patch("api.routes.completion.get_stateless_rag_chain")
async def test_completion_success_useful_context(mock_get_chain, client):
    mock_rag_answer = CompletionResponse(
        answer="Paracetamol dùng để giảm đau, hạ sốt.",
        is_useful=True
    )
    
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value={"answer": mock_rag_answer})
    mock_get_chain.return_value = mock_chain
    
    payload = {"question": "Tác dụng của Paracetamol là gì?"}
    response = await client.post("/completion", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Paracetamol dùng để giảm đau, hạ sốt."
    assert data["is_useful"] is True
    
    mock_chain.ainvoke.assert_called_once_with({"question": payload["question"]})


@pytest.mark.asyncio
@patch("api.routes.completion.get_stateless_rag_chain")
async def test_completion_success_no_context(mock_get_chain, client):
    mock_rag_answer = CompletionResponse(
        answer="Tôi không tìm thấy thông tin trong tài liệu.",
        is_useful=False
    )
    
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value={"answer": mock_rag_answer})
    mock_get_chain.return_value = mock_chain
    
    response = await client.post("/completion", json={"question": "Cách chế tạo tàu vũ trụ?"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_useful"] is False


@pytest.mark.asyncio
async def test_completion_validation_error(client):
    response = await client.post("/completion", json={})
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "question"]
    assert data["detail"][0]["type"] == "missing"


@pytest.mark.asyncio
@patch("api.routes.completion.get_stateless_rag_chain")
async def test_completion_internal_server_error(mock_get_chain, client):
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=Exception("Connection to Vector DB timeout"))
    mock_get_chain.return_value = mock_chain
    
    response = await client.post("/completion", json={"question": "Test lỗi hệ thống"})
    
    assert response.status_code == 500
