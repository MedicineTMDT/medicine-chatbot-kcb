import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from src.embeddings import get_embedding_model

load_dotenv()

def get_vector_store():

    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("Thiếu PINECONE_INDEX_NAME trong file .env")

    vector_store = PineconeVectorStore(
        index_name=index_name,
        namespace="default",
        embedding=get_embedding_model()
    )
    
    return vector_store