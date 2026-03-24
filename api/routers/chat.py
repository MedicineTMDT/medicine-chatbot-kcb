from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse
from src.chains import get_rag_chain 

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

rag_chain = get_rag_chain()

@router.post("/", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    try:
        result = rag_chain.invoke(request.question)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))