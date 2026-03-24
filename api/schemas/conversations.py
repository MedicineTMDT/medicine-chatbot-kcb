from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ConversationCreate(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True