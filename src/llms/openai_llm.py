import os
from langchain_openai import ChatOpenAI

_llm_instances = {}

def get_llm(temperature: float = 0.0, is_chat_model: bool = True) -> ChatOpenAI:
    cache_key = (temperature, is_chat_model)
    
    if cache_key not in _llm_instances:
        api_key = os.getenv("OPENAI_API_KEY", "sk-dummy-key-for-testing")
        if not api_key:
            raise ValueError("Thiếu biến môi trường OPENAI_API_KEY")

        model_name = os.getenv("CHAT_MODEL", "dummy-model") if is_chat_model else os.getenv("TITLE_MODEL", "dummy-model")
        if not model_name:
            raise ValueError("Thiếu biến môi trường tên mô hình")

        _llm_instances[cache_key] = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            max_retries=3
        )
        
    return _llm_instances[cache_key]
