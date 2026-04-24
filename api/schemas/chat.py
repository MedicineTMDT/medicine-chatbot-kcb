from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    question: str = Field(
        ..., 
        examples="Thuốc Paracetamol uống liều lượng như thế nào cho người lớn?"
    )

class DocumentMetadata(BaseModel):
    """Thông tin trích xuất của đoạn văn bản (Chunk) trong Pinecone"""
    filename: str = Field(..., description="Tên file PDF gốc (VD: Phac_do_SXH_2023.pdf)")
    page_number: int = Field(..., description="Trang số mấy trong file PDF")
    page_content: str = Field(..., description="Đoạn văn bản gốc được AI dùng làm căn cứ")
    source_link: str = Field(..., description="Link tới phác đồ kèm trang")

class ChatResponse(BaseModel):
    """Model trả về cho client theo từng chunk trong luồng SSE"""
    type: str = Field(..., description="Trạng thái stream: 'start', 'tool_start', 'stream', 'end', hoặc 'error'")
    conversation_id: Optional[uuid.UUID] = None
    answer: Optional[str] = Field(default=None, description="Từng chữ (token) được AI sinh ra, hoặc thông báo lỗi")
    sources: Optional[List[DocumentMetadata]] = Field(default=None, description="Danh sách tài liệu tham khảo (Chỉ gửi kèm ở chunk type='end')")
    warning: Optional[str] = Field(default=None, description="Cảnh báo pháp lý (Chỉ gửi kèm ở chunk type='start' hoặc 'end')")
