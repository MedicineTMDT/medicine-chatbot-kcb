from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    question: str = Field(
        ..., 
        example="Thuốc Paracetamol uống liều lượng như thế nào cho người lớn?"
    )

class DocumentMetadata(BaseModel):
    """Thông tin trích xuất của đoạn văn bản (Chunk) trong Pinecone"""
    source_file: str = Field(..., description="Tên file PDF gốc (VD: Phac_do_SXH_2023.pdf)")
    page_number: int = Field(..., description="Trang số mấy trong file PDF")
    quyet_dinh_so: str = Field(..., description="Số quyết định ban hành của Bộ Y tế")
    nam_ban_hanh: int = Field(..., description="Năm ban hành phác đồ")

    chunk_text: str = Field(..., description="Đoạn văn bản gốc được AI dùng làm căn cứ")

class ChatResponse(BaseModel):
    """Model trả về cho client sau khi AI xử lý xong"""
    conversation_id: uuid.UUID
    answer: str = Field(..., description="Câu trả lời tổng hợp của AI")
    sources: List[DocumentMetadata] = Field(
        default_factory=list, 
        description="Danh sách các nguồn tài liệu được dùng để tạo ra câu trả lời"
    )
    warning: str = Field(
        default="LƯU Ý: Đây là hệ thống AI hỗ trợ tra cứu. Vui lòng đối chiếu với phác đồ gốc trước khi ra y lệnh.",
        description="Cảnh báo pháp lý bắt buộc đối với ứng dụng y tế"
    )