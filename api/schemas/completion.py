from pydantic import BaseModel, Field

class CompletionRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi hoặc yêu cầu cần AI truy xuất và xử lý")

class CompletionResponse(BaseModel):
    answer: str = Field(..., description="Câu trả lời chi tiết cho người dùng dựa trên context.")
    is_useful: bool = Field(..., description="Trả về True nếu context cung cấp đủ thông tin để trả lời. Trả về False nếu context không liên quan hoặc không có thông tin.")
