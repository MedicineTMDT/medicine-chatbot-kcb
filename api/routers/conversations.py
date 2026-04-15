from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from db import get_db, crud
from api.schemas import ConversationResponse, ConversationCreate, ConversationUpdate, MessageResponse

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)

@router.post("/", response_model=ConversationResponse)
def create_new_conversation(conv_data: ConversationCreate, db: Session = Depends(get_db)):
    """Tạo một phiên trò chuyện mới"""

    new_conv = crud.create_conversation(db=db, user_id=conv_data.user_id, title=conv_data.title)

    return new_conv

@router.get("/", response_model=List[ConversationResponse])
def get_all_conversations(user_id: str = None, limit: int = 20, db: Session = Depends(get_db)):
    """Lấy danh sách các phiên trò chuyện (đổ ra Sidebar)"""

    conversations = crud.get_conversations_by_user(db=db, user_id=user_id, limit=limit)

    return conversations

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Lấy lịch sử tin nhắn của một phiên trò chuyện cụ thể"""

    messages = crud.get_chat_history(db=db, conversation_id=conversation_id, limit=50) # Tải 50 tin nhắn gần nhất

    if not messages:
        return []
    
    return messages

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Xóa một phiên trò chuyện và toàn bộ tin nhắn bên trong"""
    
    is_deleted = crud.delete_conversation(db=db, conversation_id=conversation_id)
    
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Conversation not found!")
        
    return {"status": "success", "message": f"Delete conversation {conversation_id} successfully"}

@router.patch("/{conversation_id}", response_model=None)
def update_conversation_manual(conversation_id: uuid.UUID, request: ConversationUpdate, db: Session = Depends(get_db)):
    updated_conv = crud.update_conversation_title(db=db, conversation_id=conversation_id, title=request.title.strip())
    
    if not updated_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"status": "success", "conversation_id": updated_conv.id, "title": updated_conv.title}
