import json
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.schemas import ChatRequest, ChatResponse, DocumentMetadata
from src.chains import get_rag_chain 
from db import get_db, crud

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/")
async def ask_question_stream(request: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    rag_chain = get_rag_chain()

    try:
        conversation_id = request.conversation_id
        if not conversation_id:
            new_conv = crud.create_conversation(db=db, user_id=request.user_id, title="New Conversation")
            conversation_id = new_conv.id

        raw_history = crud.get_chat_history(db=db, conversation_id=conversation_id, limit=6)
        chat_history = [("human" if msg.role == "user" else "ai", msg.content) for msg in raw_history]

        chain_input = {
            "question": request.question,
            "chat_history": chat_history 
        }

        crud.save_message(db=db, conversation_id=conversation_id, role="user", content=request.question)

        async def event_generator():
            full_answer = ""
            retrieved_docs = []
            
            try:
                start_chunk = ChatResponse(type="start", conversation_id=conversation_id)
                yield f"data: {start_chunk.model_dump_json()}\n\n"

                async for chunk in rag_chain.astream(chain_input):
                    
                    if "context" in chunk:
                        retrieved_docs = chunk["context"]
                        
                    elif "answer" in chunk:
                        token = chunk["answer"]
                        full_answer += token
                        
                        stream_chunk = ChatResponse(type="stream", answer=token)
                        yield f"data: {stream_chunk.model_dump_json()}\n\n"

                sources_list = [
                    DocumentMetadata(page_content=doc.page_content, **doc.metadata) for doc in retrieved_docs
                ]
                
                crud.save_message(
                    db=db, 
                    conversation_id=conversation_id, 
                    role="assistant", 
                    content=full_answer,
                    sources=[s.model_dump() for s in sources_list]
                )
                
                end_chunk = ChatResponse(type="end", sources=sources_list)
                yield f"data: {end_chunk.model_dump_json()}\n\n"

            except Exception as e:
                error_chunk = ChatResponse(type="error", answer=str(e))
                yield f"data: {error_chunk.model_dump_json()}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))