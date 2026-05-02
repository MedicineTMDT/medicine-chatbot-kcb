import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ragas import experiment, Dataset
from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory
from ragas.metrics.collections import (
    Faithfulness,
    ContextPrecision,
    ContextRecall,
)
from src.chains import get_rag_chain
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


llm = llm_factory("gpt-4o-mini", client=client, max_tokens=4096)

faithfulness = Faithfulness(llm=llm)
context_precision = ContextPrecision(llm=llm)
context_recall = ContextRecall(llm=llm)

RATE_LIMIT_SEMAPHORE = asyncio.Semaphore(4)

@experiment()
async def evaluate_core_rag(row):
    async with RATE_LIMIT_SEMAPHORE:
        question = row["user_input"]
        
        rag_chain = get_rag_chain()
        
        full_answer = ""
        retrieved_contexts = []
        
        try:
            async for chunk in rag_chain.astream({
                "question": question,
                "chat_history": [] 
            }):
                if "context" in chunk:
                    retrieved_contexts = [doc.page_content for doc in chunk["context"]]
                elif "answer" in chunk:
                    full_answer += chunk["answer"]
                    
        except Exception as e:
            print(f"Lỗi khi chạy chain với câu hỏi '{question}': {e}")
            return

        sample = {
            "user_input": row["user_input"],
            "response": full_answer.strip(),
            "retrieved_contexts": retrieved_contexts,
            "reference": row["reference"]
        }

        scores = {}
        scores["faithfulness"] = await faithfulness.ascore(user_input=sample["user_input"], response=sample["response"], retrieved_contexts=sample["retrieved_contexts"])
        scores["context_precision"] = await context_precision.ascore(user_input=sample["user_input"], reference=sample["reference"], retrieved_contexts=sample["retrieved_contexts"])
        scores["context_recall"] = await context_recall.ascore(user_input=sample["user_input"], reference=sample["reference"], retrieved_contexts=sample["retrieved_contexts"])

        return {**sample, **scores}

async def main():
    DATASET_NAME = "test_data"
    
    ROOT_DIR = "evaluate/datasets" 
    
    try:
        print(f"📂 Đang tải dữ liệu từ CSV ({DATASET_NAME}.csv) tại '{ROOT_DIR}'...")
        test_data = Dataset.load(name=DATASET_NAME, backend="local/csv", root_dir="evaluate")
        
    except Exception as e:
        print(f"Lỗi khi load dataset: {e}")
        return

    print("🚀 Bắt đầu giả lập RAG pipeline và chấm điểm...")

    results = await evaluate_core_rag.arun(test_data)
    
    print("\n📊 Điểm số trung bình hệ thống RAG của bạn:")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
