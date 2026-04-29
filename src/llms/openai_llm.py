import os
from langchain_openai import ChatOpenAI

def get_llm(temperature: float = 0.0, is_chat_model: bool = True) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu biến môi trường OPENAI_API_KEY")

    model_name = os.getenv("CHAT_MODEL") if is_chat_model else os.getenv("TITLE_MODEL")
    if not model_name:
        raise ValueError("Thiếu biến môi trường tên mô hình")

    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        api_key=api_key,
        max_retries=3
    )
    
    return llm
