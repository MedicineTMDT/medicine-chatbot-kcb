import json
import os
import uuid
from fastapi import APIRouter, HTTPException, Depends 
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas import ChatRequest
from src.services import ChatStreamHandler
from db import get_db

router = APIRouter(
    prefix="/conversations",
    tags=["Chat Operation"]
)

BASE_URL_FILE = os.getenv("BASE_URL_FILE")

@router.post("/{conversation_id}/messages")
async def ask_question_stream(conversation_id: uuid.UUID, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        handler = ChatStreamHandler(
            db=db, 
            conversation_id=conversation_id, 
            question=request.question
        )
        return StreamingResponse(handler.stream_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
