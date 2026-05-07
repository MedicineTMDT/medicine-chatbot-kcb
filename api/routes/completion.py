from fastapi import APIRouter, HTTPException
from api.schemas.completion import CompletionRequest, CompletionResponse

from src.chains import get_stateless_rag_chain 

router = APIRouter(
        prefix="",            
        tags=["Stateless Completions"]
)


@router.post("/completion", response_model=CompletionResponse)
async def generate_stateless_completion(request: CompletionRequest):
    try:
        rag_chain = get_stateless_rag_chain()
        
        result = await rag_chain.ainvoke({
            "question": request.question
        })
        
        return result["answer"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
