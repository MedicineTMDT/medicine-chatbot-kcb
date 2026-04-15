import os
from langchain_openai import OpenAIEmbeddings

def get_embedding_model() -> OpenAIEmbeddings:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu biến môi trường OPENAI_API_KEY")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=api_key,
        max_retries=3
    )
    
    return embeddings
