import pytest
from src.tools import search_drug, check_drug_interactions

@pytest.mark.asyncio
async def test_integration_search_drug_success():
    result = await search_drug("Paracetamol")
    
    assert "error" not in result
    assert result.get("name") is not None
    assert result.get("metadata") is not None

@pytest.mark.asyncio
async def test_integration_search_drug_not_found():
    result = await search_drug("ThuocGiaDinhKhongTonTai123")
    
    assert "error" in result
    assert "Không tìm thấy" in result["error"]

@pytest.mark.asyncio
async def test_integration_check_interactions_success():
    ingredients = ["Aspirin", "Ibuprofen"]
    result = await check_drug_interactions(ingredients)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "severity" in result[0]
    assert "description" in result[0]

@pytest.mark.asyncio
async def test_integration_check_interactions_empty_safe():
    ingredients = ["Vitamin C", "Vitamin B1"]
    result = await check_drug_interactions(ingredients)
    
    assert isinstance(result, dict)
    assert "message" in result
    assert "Không tìm thấy tương tác bất lợi nào" in result["message"]

