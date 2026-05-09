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
        rag_chain = get_stateless_rag_chain()
        
        result = await rag_chain.ainvoke({
            "question": request.question
        })
        
        return result["answer"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_prescription(request: CompletionRequest):
    """
    Analyzes a prescription (sent as a string or stringified JSON in the 'question' field).
    Returns a comprehensive analysis including drug summaries, warnings, and usage advice.
    """
    try:
        analysis_chain = get_prescription_analysis_chain()
        
        result = await analysis_chain.ainvoke({
            "question": request.question
        })
        
        return {"answer": result["answer"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
