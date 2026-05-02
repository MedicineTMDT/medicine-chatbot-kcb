import json
import uuid
import os
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv
from src.prompts import build_rag_prompt

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

RAG_PROMPT_TEMPLATE = build_rag_prompt()

class QAPair(BaseModel):
    query: str = Field(..., description="Câu hỏi thực tế người dùng/bác sĩ có thể hỏi dựa trên context.")
    expected_output: str = Field(..., description="Câu trả lời chuẩn xác, tuân thủ tuyệt đối văn phong của RAG_PROMPT.")

class BootstrappedData(BaseModel):
    qa_pairs: List[QAPair] = Field(..., description="Danh sách 1-2 cặp câu hỏi và trả lời.")

def generate_draft_qa(chunk_text: str) -> BootstrappedData:
    system_instruction = f"""
    Bạn là một chuyên gia dữ liệu y tế đang tạo tập 'Golden Dataset' để kiểm thử hệ thống RAG.
    Nhiệm vụ: Đọc Context và tạo ra 1 đến 2 cặp Câu hỏi (query) và Câu trả lời (expected_output).

    YÊU CẦU QUAN TRỌNG CHO CÂU HỎI ('query'):
    1. Đóng vai thực tế (Persona): Câu hỏi phải mô phỏng cách hỏi tự nhiên của Bác sĩ, Dược sĩ, hoặc Bệnh nhân đang nhắn tin với Chatbot.
        - Ví dụ TỐT: "Trẻ em 15kg bị sốt thì uống Paracetamol liều tối đa một ngày là bao nhiêu?"
        - Ví dụ XẤU: "Nêu liều lượng Paracetamol cho trẻ em theo phác đồ."
    2. Đa dạng hóa: Đừng chỉ hỏi định nghĩa. Hãy hỏi về: Liều lượng cụ thể, Chống chỉ định, Tương tác thuốc, hoặc Cách xử trí tác dụng phụ (nếu Context có nhắc đến).
    
    YÊU CẦU QUAN TRỌNG CHO 'expected_output':
    1. Trả lời PHẢI dựa hoàn toàn vào Context.
    2. Phải mô phỏng ĐÚNG văn phong của hệ thống Chatbot khi được gọi với prompt sau:
    ---
    {RAG_PROMPT_TEMPLATE}
    ---
    (Giả định <CHAT_HISTORY> đang trống, chỉ tập trung trả lời câu hỏi dựa trên <CONTEXT>).
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Context:\n{chunk_text}"}
        ],
        response_format=BootstrappedData,
        temperature=0.1
    )
    
    return completion.choices[0].message.parsed


def run_hitl_pipeline(input_file: str = "evaluate/output/selected_50_chunks.json", output_file: str = "evaluate/output/eval_dataset.jsonl"):
    print("🚀 Khởi động công cụ HITL Dataset Builder...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {input_file}.")
        return

    with open(output_file, 'a', encoding='utf-8') as out_f:
        for i, chunk_data in enumerate(chunks):
            chunk_id = chunk_data.get('id', str(uuid.uuid4()))
            chunk_text = chunk_data.get('text', '')
            original_metadata = chunk_data.get('metadata', {})
            
            print(f"\n{'-'*60}")
            print(f"📄 Đang xử lý Chunk {i+1}/{len(chunks)} [ID: {chunk_id}]")
            
            meta_for_llm = {k: v for k, v in original_metadata.items() if k != 'text'}
            
            rich_context = f"""
            [THÔNG TIN BỔ SUNG TỪ METADATA]
            {json.dumps(meta_for_llm, ensure_ascii=False, indent=2)}
            
            [NỘI DUNG CHÍNH CỦA PHÁC ĐỒ]
            {chunk_text}
            """
            
            try:
                llm_output = generate_draft_qa(rich_context)
            except Exception as e:
                print(f"❌ Lỗi gọi LLM: {e}")
                continue
            
            for qa_idx, qa in enumerate(llm_output.qa_pairs):
                print(f"\n[Mẫu {qa_idx + 1}]")
                print(f"🔹 Context: {chunk_text}")
                print(f"🟢 Query: {qa.query}")
                print(f"🟡 Expected Output:\n{qa.expected_output}")
                
                while True:
                    action = input("\nHành động: [A]ccept | [R]eject | [E]dit Query | [O]dit Output : ").strip().upper()
                    
                    final_query = qa.query
                    final_output = qa.expected_output
                    is_saved = False
                    
                    if action == 'R':
                        print("❌ Đã bỏ qua mẫu này.")
                        break
                    
                    elif action == 'E':
                        final_query = input("Nhập Query mới: ")
                        is_saved = True
                        
                    elif action == 'O':
                        print("Nhập Expected Output mới (nhấn Enter để hoàn tất dòng, viết \n để xuống dòng nếu cần - Hoặc copy paste trực tiếp):")
                        final_output = input("> ")
                        is_saved = True
                        
                    elif action == 'A':
                        is_saved = True
                        
                    else:
                        print("⚠️ Lựa chọn không hợp lệ.")
                        continue
                    
                    if is_saved:
                        dataset_record = {
                            "query": final_query,
                            "expected_output": final_output,
                            "metadata": {
                                "source_chunk_id": chunk_id,
                                "context_used": chunk_text,
                                "original_metadata": chunk_data.get('metadata', {})
                            }
                        }
                        out_f.write(json.dumps(dataset_record, ensure_ascii=False) + '\n')
                        print("✅ Đã lưu vào eval_dataset.jsonl")
                        break

if __name__ == "__main__":
    run_hitl_pipeline()
    print("\n🎉 HITL Session kết thúc. Kiểm tra file eval_dataset.jsonl")
