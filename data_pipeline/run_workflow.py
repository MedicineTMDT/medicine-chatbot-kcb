import json
import os 
import time
import concurrent.futures
from dotenv import load_dotenv
from unstructured_client import UnstructuredClient
from unstructured_client.models import operations, shared

load_dotenv()

def process_single_file(input_file, client):
    base_name = os.path.basename(input_file).replace(".pdf", "")
    output_file = f"./output/{base_name}_results.json"

    print(f"\n[Luồng {base_name}] ĐANG BẮT ĐẦU XỬ LÝ FILE: {input_file}")

    if not os.path.exists(input_file):
        print(f"[Luồng {base_name}] ⚠️ Cảnh báo: Không tìm thấy file, bỏ qua...")
        return

    with open(input_file, "rb") as f:
        file_content = f.read()

    job_config = {
        "job_nodes": [
            {
                "name": "Partitioner",
                "type": "partition",
                "subtype": "unstructured_api",
                "settings": {
                        "strategy": "hi_res",
                        "languages": ["vie"],
                        "is_dynamic": True,
                        "include_page_breaks": False,
                        "infer_table_structure": False,
                        "exclude_elements": [],
                        "coordinates": True,
                        "extract_image_block_types": [
                                    "Image", "Table", "Title", "Text",
                                    "UncategorizedText", "NarrativeText",
                                    "BulletedText", "Paragraph", "Abstract",
                                    "Threading", "Form", "CompositeElement",
                                    "Picture", "FigureCaption", "Figure",
                                    "Caption", "List", "ListItem",
                                    "List-item", "Formula", "FormKeysValues",
                                    "Header"
                        ],
                        "pdf_infer_table_structure": False,
                        "xml_keep_tags": False,
                        "encoding": "utf-8",
                        "provider": None
            },
            },
            {
                "name": "Table to HTML",
                "type": "prompter",
                "subtype": "twopass_table2html",
                "settings": {
                        "model": ["gpt-5-mini", "claude-sonnet-4-20250514"],
                        "provider_type": ["openai", "anthropic"]
            },
            },
            {
                "name": "Generative OCR",
                "type": "prompter",
                "subtype": "openai_ocr",
                "settings": {
                        "model": "gpt-4o",
                        "provider_type": "openai"
            },
            },
            {
                "name": "Image Description",
                "type": "prompter",
                "subtype": "openai_image_description",
                "settings": {
                        "model": "gpt-4o",
                        "provider_type": "openai"
            },
            },
            {
                "name": "Chunker",
                "type": "chunk",
                "subtype": "chunk_by_title",
                "settings": {
                        "combine_text_under_n_chars": None,
                        "include_orig_elements": False,
                        "max_characters": 2048,
                        "multipage_sections": True,
                        "new_after_n_chars": 1500,
                        "overlap": 160,
                        "overlap_all": False,
                        "contextual_chunking_strategy": "v1",
                        "contextual_chunking_model": None,
                        "unstructured_api_url": None,
                        "unstructured_api_key": None,
                        "skip_table_chunking": False,
                        "contextual_chunking_service_name": None,
                        "contextual_chunking_auth": None
            },
            },
            {
                "name": "Embedder",
                "type": "embed",
                "subtype": "azure_openai",
                "settings": {
                        "model_name": "text-embedding-3-large"
            },
            }
        ],
    }

    print(f"[Luồng {base_name}] STEP 1: Creating Job...")
    try:
        create_response = client.jobs.create_job(
            request=operations.CreateJobRequest(
                body_create_job=shared.BodyCreateJob(
                    request_data=json.dumps(job_config),
                    input_files=[
                        shared.InputFiles(
                            content=file_content,
                            file_name=os.path.basename(input_file),
                            content_type="application/pdf",
                        )
                    ],
                )
            )
        )
    except Exception as e:
        print(f"[Luồng {base_name}] ❌ Lỗi tạo Job: {e}")
        return

    job_id = create_response.job_information.id
    file_id = create_response.job_information.input_file_ids[0]

    print(f"[Luồng {base_name}] ✓ Job created: ID {job_id}")

    print(f"[Luồng {base_name}] STEP 2: Monitoring Progress...")
    start_time = time.time()
    job_failed = False
    
    while True:
        status_response = client.jobs.get_job(
            request=operations.GetJobRequest(job_id=job_id)
        )

        status = status_response.job_information.status
        elapsed = int(time.time() - start_time)
        
        print(f"[Luồng {base_name}] Trạng thái: {status} (sau {elapsed}s)")

        if status == "COMPLETED":
            print(f"[Luồng {base_name}] ✓ Hoàn thành phân tích (mất {elapsed}s)")
            break
        elif status in ["FAILED", "CANCELLED"]:
            print(f"[Luồng {base_name}] ✗ Job thất bại hoặc bị hủy.")
            job_failed = True
            break

        time.sleep(10)

    if job_failed:
        return

    print(f"[Luồng {base_name}] STEP 3: Downloading Results...")
    try:
        download_response = client.jobs.download_job_output(
            request=operations.DownloadJobOutputRequest(job_id=job_id, file_id=file_id)
        )

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(download_response.any, f, indent=2, ensure_ascii=False)

        print(f"[Luồng {base_name}] ✓ Đã lưu thành công: {output_file}")
        print(f"[Luồng {base_name}]   Số Elements trích xuất: {len(download_response.any)}")
    except Exception as e:
         print(f"[Luồng {base_name}] ❌ Lỗi tải kết quả (404/Timeout): {e}")

def main():
    UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY", "<your-api-key>")
    UNSTRUCTURED_API_URL = os.getenv(
        "UNSTRUCTURED_API_URL", "https://platform.unstructuredapp.io"
    )

    INPUT_FILES = [
        "files/1832_QD-BYT.pdf", 
        "files/3879_QD-BYT.pdf", 
    ]

    client = UnstructuredClient(
        api_key_auth=UNSTRUCTURED_API_KEY, server_url=UNSTRUCTURED_API_URL
    )

    print("=" * 80)
    print(f"BẮT ĐẦU CHẠY ĐA LUỒNG CHO {len(INPUT_FILES)} FILE")
    print("=" * 80)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i, f in enumerate(INPUT_FILES):
            future = executor.submit(process_single_file, f, client)
            futures.append(future)
            
            if i < len(INPUT_FILES) - 1:
                print(f"⏳ Đang chờ 5 giây trước khi gửi API cho file tiếp theo...")
                time.sleep(5) 
        
        concurrent.futures.wait(futures)

    print("\n" + "=" * 80)
    print("✓ TẤT CẢ CÁC FILE ĐÃ ĐƯỢC XỬ LÝ XONG!")
    print("=" * 80)

if __name__ == "__main__":
    main()
