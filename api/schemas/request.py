from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(
        ..., 
        example="Thuốc Paracetamol uống liều lượng như thế nào cho người lớn?"
    )