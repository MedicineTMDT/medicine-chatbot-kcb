import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone

def chunker(seq, size):
    """Hàm hỗ trợ chia nhỏ danh sách (list) thành các lô (batch) có kích thước đều nhau"""
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def push_to_pinecone(input_file):
    load_dotenv()
    
    API_KEY = os.getenv("PINECONE_API_KEY")
    INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    NAMESPACE = "default" (Cú pháp cho SDK v3+)
    pc = Pinecone(api_key=API_KEY)
    index = pc.Index(INDEX_NAME)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"❌ Không tìm thấy file: {input_file}")
        
    with open(input_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
        
    total_records = len(records)
    print(f"📄 Đã đọc {total_records} bản ghi. Bắt đầu đẩy lên index '{INDEX_NAME}'...")

    if total_records > 0 and not records[0].get("values"):
        print("⚠️ CẢNH BÁO: Mảng 'values' (vector) đang trống. Pinecone sẽ báo lỗi nếu bạn không có vector thực tế.")

    BATCH_SIZE = 100
    
    for i, batch in enumerate(chunker(records, BATCH_SIZE)):
        try:
            index.upsert(vectors=batch, namespace=NAMESPACE)
            print(f"✅ Đã đẩy thành công lô {i + 1} (Chứa {len(batch)} bản ghi)")
        except Exception as e:
            print(f"❌ Lỗi khi đẩy lô {i + 1}: {e}")

    print("🎉 Hoàn tất quá trình tải dữ liệu lên Pinecone!")

if __name__ == "__main__":
    DATA_FILE = "output/pinecone_records.json" 
    push_to_pinecone(DATA_FILE)
