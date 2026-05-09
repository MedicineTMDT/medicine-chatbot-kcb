from fastapi import APIRouter, HTTPException
from api.schemas.completion import CompletionRequest, CompletionResponse

from src.chains import get_stateless_rag_chain, get_prescription_analysis_chain

router = APIRouter(
        prefix="",            
        tags=["Stateless Completions"]
)


@router.post("/completion", response_model=CompletionResponse)
async def generate_stateless_completion(request: CompletionRequest):
    try:
        analysis_chain = get_prescription_analysis_chain()
        result = await analysis_chain.ainvoke({
            "question": request.question
        })
        
        return CompletionResponse(
            answer=result["answer"],
            is_useful=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
