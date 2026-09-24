import pytest
import respx
import httpx
from src.tools import search_drug, check_drug_interactions

SPRING_MOCK_URL = "http://localhost:8080"
INTERACTION_PATH = "/api/v1/drug-interactions/search-by-ingredients"

@pytest.mark.asyncio
@respx.mock
async def test_search_drug_success():
    """Kịch bản: Tìm thấy thuốc và lấy chi tiết thành công"""
    
    respx.get(f"{SPRING_MOCK_URL}/api/v1/drugs/search?name=Paracetamol").respond(
        status_code=200,
        json={
            "result": {
                "content": [{"id": "drug-123", "name": "Paracetamol"}]
            }
        }
    )

    respx.get(f"{SPRING_MOCK_URL}/api/v1/drugs/drug-123").respond(
        status_code=200,
        json={
            "result": {
                "id": "drug-123",
                "name": "Paracetamol",
                "uses": "Giảm đau, hạ sốt"
            }
        }
    )

    result = await search_drug("Paracetamol")

    assert "error" not in result
    assert result["name"] == "Paracetamol"
    assert result["uses"] == "Giảm đau, hạ sốt"


@pytest.mark.asyncio
@respx.mock
async def test_search_drug_not_found():
    """Kịch bản: API Spring Boot trả về danh sách rỗng"""
    
    respx.get(f"{SPRING_MOCK_URL}/api/v1/drugs/search?name=ThuocLa").respond(
        status_code=200,
        json={"result": {"content": []}}
    )

    result = await search_drug("ThuocLa")

    assert "error" in result
    assert "Không tìm thấy" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_search_drug_network_timeout():
    """Kịch bản: Spring Boot API bị treo, httpx văng lỗi Timeout"""
    
    respx.get(f"{SPRING_MOCK_URL}/api/v1/drugs/search?name=Hapacol").mock(
        side_effect=httpx.TimeoutException("Read timeout")
    )

    result = await search_drug("Hapacol")

    assert "error" in result
    assert "Lỗi hệ thống medicine_service" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_check_interactions_success():
    respx.get(url__regex=f"^{SPRING_MOCK_URL}{INTERACTION_PATH}").respond(
        status_code=200,
        json={
            "result": [
                {
                    "severity": "Nghiêm trọng",
                    "description": "Nguy cơ xuất huyết tiêu hóa cao khi dùng chung.",
                    "mechanism": "Cả hai đều là NSAID."
                }
            ]
        }
    )

    ingredients = ["Aspirin", "Ibuprofen"]
    result = await check_drug_interactions(ingredients)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["severity"] == "Nghiêm trọng"
    assert "xuất huyết" in result[0]["description"]


@pytest.mark.asyncio
@respx.mock
async def test_check_interactions_empty_safe():
    respx.get(url__regex=f"^{SPRING_MOCK_URL}{INTERACTION_PATH}").respond(
        status_code=200,
        json={"result": []}
    )

    ingredients = ["Vitamin C", "Vitamin B1"]
    result = await check_drug_interactions(ingredients)

    assert isinstance(result, dict)
    assert "message" in result
    assert "Không tìm thấy tương tác bất lợi nào" in result["message"]


@pytest.mark.asyncio
@respx.mock
async def test_check_interactions_http_error():
    respx.get(url__regex=f"^{SPRING_MOCK_URL}{INTERACTION_PATH}").respond(
        status_code=500,
        json={"error": "Internal Server Error"}
    )

    ingredients = ["Paracetamol", "Ibuprofen"]
    result = await check_drug_interactions(ingredients)

    assert isinstance(result, dict)
    assert "error" in result
    assert "Lỗi hệ thống medicine_service" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_check_interactions_network_timeout():
    respx.get(url__regex=f"^{SPRING_MOCK_URL}{INTERACTION_PATH}").mock(
        side_effect=httpx.TimeoutException("Connection timeout")
    )

    ingredients = ["Warfarin", "Aspirin"]
    result = await check_drug_interactions(ingredients)

    assert isinstance(result, dict)
    assert "error" in result
    assert "Lỗi hệ thống medicine_service" in result["error"]
    assert "timeout" in result["error"].lower()
