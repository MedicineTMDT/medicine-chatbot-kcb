from pydantic import BaseModel, Field

class TitleRequest(BaseModel):
    question: str = Field(..., description="Nội dung tin nhắn đầu tiên để tóm tắt")
