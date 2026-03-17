import json
import os
import time
from unstructured_client import UnstructuredClient
from unstructured_client.models import operations, shared

def main():
    UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY")
    UNSTRUCTURED_API_URL = "https://platform.unstructuredapp.io/api/v1"

    INPUT_DIR = "./files"
    OUTPUT_FILE = "./output/results.json"

    client = UnstructuredClient(
        api_key_auth=UNSTRUCTURED_API_KEY, server_url=UNSTRUCTURED_API_URL
    )

    print("=" * 80)
    print("STEP 1: Create Ephemeral Job with Custom Pipeline")
    print("=" * 80)

    input_files_list = []
    if os.path.exists(INPUT_DIR):
        for filename in os.listdir(INPUT_DIR):
            filepath = os.path.join(INPUT_DIR, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    input_files_list.append(
                        shared.InputFiles(
                            content=f.read(),
                            file_name=filename,
                            content_type="application/pdf",
                        )
                    )
    
    if not input_files_list:
        print(f"No files found in {INPUT_DIR}")
        return
    # -------------------------------------------------

    job_config = {
        "job_nodes": [
            {
                "name": "Partitioner",
                "type": "partition",
                "subtype": "unstructured_api",
                "settings": {
                        "strategy": "hi_res",
                        "include_page_breaks": False,
                        "infer_table_structure": False,
                        "coordinates": True,
                        "extract_image_block_types": [
                                    "Title", "Text", "UncategorizedText", "NarrativeText",
                                    "BulletedText", "Paragraph", "Abstract", "Threading",
                                    "Form", "CompositeElement", "Image", "Picture",
                                    "FigureCaption", "Figure", "Caption", "List",
                                    "ListItem", "List-item", "Table", "Formula",
                                    "CodeSnippet", "FormKeysValues", "Header"
                        ]
            },
            },
            {
                "name": "Table to HTML",
                "type": "prompter",
                "subtype": "anthropic_table2html",
                "settings": {
                        "model": "claude-opus-4-5-20251101"
            },
            },
            {
                "name": "Enrichment",
                "type": "prompter",
                "subtype": "anthropic_ocr",
                "settings": {
                        "model": "claude-opus-4-5-20251101"
            },
            },
            {
                "name": "Enrichment",
                "type": "prompter",
                "subtype": "openai_image_description",
                "settings": {
                        "prompt_interface_overrides": None,
                        "model": "gpt-4o"
            },
            },
            {
                "name": "Chunker",
                "type": "chunk",
                "subtype": "chunk_by_title",
                "settings": {
                        "include_orig_elements": False,
                        "max_characters": 2048,
                        "multipage_sections": False,
                        "new_after_n_chars": 1500,
                        "overlap": 160,
                        "overlap_all": False,
                        "contextual_chunking_strategy": None
            },
            }
        ],
    }

    create_response = client.jobs.create_job(
        request=operations.CreateJobRequest(
            body_create_job=shared.BodyCreateJob(
                request_data=json.dumps(job_config),
                input_files=input_files_list,
            )
        )
    )

    job_id = create_response.job_information.id
    file_ids = create_response.job_information.input_file_ids 

    print(f"\n✓ Job created successfully")
    print(f"  Job ID: {job_id}")
    print(f"  File IDs: {file_ids}")
    print(f"  Job Type: {create_response.job_information.job_type}")
    print(f"  Status: {create_response.job_information.status}")

    if hasattr(create_response.job_information, "output_node_files"):
        print(f"\n  Pipeline nodes:")
        for node_file in create_response.job_information.output_node_files:
            print(f"    - {node_file.node_type}/{node_file.node_subtype}")

    print("\n" + "=" * 80)
    print("STEP 2: Monitor Job Progress")
    print("=" * 80)

    start_time = time.time()
    while True:
        status_response = client.jobs.get_job(
            request=operations.GetJobRequest(job_id=job_id)
        )

        status = status_response.job_information.status
        elapsed = int(time.time() - start_time)
        print(f"Status: {status} (elapsed: {elapsed}s)    ", end="\r")

        if status == "COMPLETED":
            print(f"\n✓ Job completed successfully (took {elapsed}s)")
            break
        elif status in ["FAILED", "CANCELLED"]:
            print(f"\n✗ Job {status.lower()}")
            exit(1)

        time.sleep(5)

    print("\n" + "=" * 80)
    print("STEP 3: Download Results")
    print("=" * 80)

    all_results = []
    
    for f_id in file_ids:
        print(f"Downloading results for file ID: {f_id}...")
        try:
            download_response = client.jobs.download_job_output(
                request=operations.DownloadJobOutputRequest(job_id=job_id, file_id=f_id)
            )
            all_results.extend(download_response.any)
        except Exception as e:
            print(f"Failed to download {f_id}: {e}")

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2) # Lưu list tổng hợp
    # ----------------------------------------------------------------

    print(f"✓ All results saved to: {OUTPUT_FILE}")
    print(f"  Total elements extracted: {len(all_results)}")

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()