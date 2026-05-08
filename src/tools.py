import os
import httpx
from typing import List, Dict, Any

SPRING_API_BASE_URL = os.getenv("SPRING_API_BASE_URL", "http://localhost:8080")
TIMEOUT = 10.0

async def search_drug(name: str) -> Dict[str, Any]:
    """
    Search for a drug by name and return full details of the first match.
    Internal pipeline: search drugs -> get first result ID -> get drug details.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 1. Search for the drug
            search_url = f"{SPRING_API_BASE_URL}/api/v1/drugs/search"
            search_response = await client.get(search_url, params={"name": name})
            search_response.raise_for_status()
            search_data = search_response.json()

            # APIResponse<Page<DrugSimpleResponse>>
            results = search_data.get("result", {}).get("content", [])
            if not results:
                return {"error": f"Không tìm thấy thông tin cho thuốc '{name}'."}

            # 2. Get full details for the first result
            drug_id = results[0].get("id")
            detail_url = f"{SPRING_API_BASE_URL}/api/v1/drugs/{drug_id}"
            detail_response = await client.get(detail_url)
            detail_response.raise_for_status()
            detail_data = detail_response.json()

            return detail_data.get("result", {})

    except httpx.HTTPError as e:
        return {"error": f"Lỗi hệ thống medicine_service (Drug Search): {str(e)}"}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {str(e)}"}

async def check_drug_interactions(ingredient_names: List[str]) -> Any:
    """
    Check for interactions between multiple medicine ingredients.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            interaction_url = f"{SPRING_API_BASE_URL}/api/v1/drug-interactions/search-by-ingredients"
            # ingredientNames in Spring Boot is mapped from multiple query params with same name
            response = await client.get(interaction_url, params={"ingredientNames": ingredient_names})
            response.raise_for_status()
            interaction_data = response.json()

            results = interaction_data.get("result", [])
            if not results:
                return {"message": "Không tìm thấy tương tác bất lợi nào giữa các hoạt chất này trong cơ sở dữ liệu."}
            
            return results

    except httpx.HTTPError as e:
        return {"error": f"Lỗi hệ thống medicine_service (Interactions): {str(e)}"}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {str(e)}"}

def get_medicine_tools_definition():
    """
    Returns OpenAI tool definitions for medicine lookup and interactions.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_drug",
                "description": "Tra cứu thông tin chi tiết về một loại thuốc (công dụng, liều dùng, thành phần, tác dụng phụ).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Tên thuốc hoặc hoạt chất cần tra cứu (VD: 'Paracetamol', 'Hapacol')"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_drug_interactions",
                "description": "Kiểm tra tương tác giữa hai hoặc nhiều hoạt chất/thuốc khi dùng chung.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ingredient_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Danh sách tên các hoạt chất hoặc tên thuốc cần kiểm tra tương tác (VD: ['Paracetamol', 'Ibuprofen'])"
                        }
                    },
                    "required": ["ingredient_names"]
                }
            }
        }
    ]

# Mapping function names to implementation
AVAILABLE_TOOLS = {
    "search_drug": search_drug,
    "check_drug_interactions": check_drug_interactions
}
