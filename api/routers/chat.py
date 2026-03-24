from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
from api.schemas import ChatRequest, ChatResponse
from src.chains import get_rag_chain 
from db import get_db, crud

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/", response_model=ChatResponse)
async def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    rag_chain = get_rag_chain()

    try:
        conversation_id = request.conversation_id
        
        if not conversation_id:
            new_conv = crud.create_conversation(db=db, title="New Conversation")
            conversation_id = new_conv.id

        raw_history = crud.get_chat_history(db=db, conversation_id=conversation_id, limit=6)
        
        chat_history = []
        for msg in raw_history:
            role = "human" if msg.role == "user" else "ai"
            chat_history.append((role, msg.content))

        chain_input = {
            "question": request.question,
            "chat_history": chat_history 
        }
        
        result = rag_chain.invoke(chain_input)
        
        answer = result["answer"] if isinstance(result, dict) and "answer" in result else str(result)
        
        crud.save_message(db=db, conversation_id=conversation_id, role="user", content=request.question)
        crud.save_message(db=db, conversation_id=conversation_id, role="assistant", content=answer)

        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))