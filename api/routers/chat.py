from fastapi import APIRouter, HTTPException
from api.schemas.request import ChatRequest
from api.schemas.response import ChatResponse
from src.chains import get_rag_chain 

router = APIRouter()

rag_chain = get_rag_chain()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    try:
        result = rag_chain.invoke(request.question)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))