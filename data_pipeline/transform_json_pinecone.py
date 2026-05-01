import json
import uuid
import random
import string
import re

def generate_pinecone_id():
    chars = string.ascii_letters + string.digits + "_-"
    prefix = "1-" + "".join(random.choices(chars, k=31))
    suffix = str(uuid.uuid4())
    return f"{prefix}#{suffix}"

def clean_filename(filename):
    if not filename:
        return ""
    return re.sub(r'-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)$', r'\1', filename)

def convert_to_pinecone_format(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
        
    pinecone_records = []
    
    for record in records:
        old_metadata = record.get("metadata", {})
        
        new_metadata = {
            "element_id": record.get("element_id"),
            "filename": clean_filename(old_metadata.get("filename")),
            "page_number": old_metadata.get("page_number"),
            "text": record.get("text", "")
        }
        
        if "text_as_html" in old_metadata:
            new_metadata["text_as_html"] = old_metadata["text_as_html"]
            
        pinecone_record = {
            "id": generate_pinecone_id(),
            "values": record.get("embeddings", []),
            "metadata": new_metadata
        }
        
        pinecone_records.append(pinecone_record)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pinecone_records, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã chuyển đổi thành công {len(pinecone_records)} bản ghi!")
    print(f"📁 File kết quả được lưu tại: {output_file}")

# ================= KÍCH HOẠT =================
if __name__ == "__main__":
    INPUT_FILEPATH = "output/5643_QD-BYT_results.json"
    OUTPUT_FILEPATH = "output/pinecone_records.json"
    
    convert_to_pinecone_format(INPUT_FILEPATH, OUTPUT_FILEPATH)
