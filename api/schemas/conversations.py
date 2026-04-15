from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ConversationCreate(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = "New Conversation"

class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[str] = None
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)

class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    sources: Optional[list] = None

    class Config:
        from_attributes = True

