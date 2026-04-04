import asyncio
import os
from dotenv import load_dotenv
from src.chains import get_rag_chain

load_dotenv()

async def verify_conversational_rag():
    print("--- Testing Conversational RAG ---")
    chain = get_rag_chain()
    
    # Simulating Turn 1
    print("\nTurn 1: Liều dùng Paracetamol người lớn?")
    chat_history = []
    input_1 = {
        "question": "Liều dùng Paracetamol người lớn?",
        "chat_history": chat_history
    }
    
    answer_1 = ""
    async for chunk in chain.astream(input_1):
        if "answer" in chunk:
            answer_1 += chunk["answer"]
    
    print(f"AI Answer 1: {answer_1[:100]}...")
    
    # Simulating Turn 2 (Ambiguous follow-up)
    print("\nTurn 2: còn trẻ em thì sao?")
    chat_history.append(("human", "Liều dùng Paracetamol người lớn?"))
    chat_history.append(("ai", answer_1))
    
    input_2 = {
        "question": "còn trẻ em thì sao?",
        "chat_history": chat_history
    }
    
    standalone_q = ""
    context_found = False
    answer_2 = ""
    
    async for chunk in chain.astream(input_2):
        if "standalone_question" in chunk:
            standalone_q = chunk["standalone_question"]
            print(f"✓ Standalone Question Generated: {standalone_q}")
        if "context" in chunk:
            context_found = len(chunk["context"]) > 0
            print(f"✓ Context Found: {context_found} (Docs found: {len(chunk['context'])})")
        if "answer" in chunk:
            answer_2 += chunk["answer"]
            
    print(f"\nAI Answer 2: {answer_2}")
    
    # Assertions
    if "Paracetamol" in standalone_q and "trẻ em" in standalone_q:
        print("\nSUCCESS: Standalone question contains correct context.")
    else:
        print("\nFAILURE: Standalone question is missing context.")

    if context_found and "Xin lỗi" not in answer_2:
        print("SUCCESS: AI successfully answered the follow-up using context.")
    else:
        print("FAILURE: AI failed to answer the follow-up.")

if __name__ == "__main__":
    asyncio.run(verify_conversational_rag())
