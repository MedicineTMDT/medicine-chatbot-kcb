import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm(temperature: float = 0.0, model_name: str = "gpt-4o") -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu biến môi trường OPENAI_API_KEY")

    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        api_key=api_key,
        max_retries=3
    )
    
    return llm