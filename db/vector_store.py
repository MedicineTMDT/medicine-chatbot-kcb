import os
from langchain_pinecone import PineconeVectorStore
from src.embeddings import get_embedding_model

_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        if "PINECONE_API_KEY" not in os.environ:
            os.environ["PINECONE_API_KEY"] = "dummy-pinecone-key"

        index_name = os.getenv("PINECONE_INDEX_NAME", "dummy-index")

        _vector_store_instance = PineconeVectorStore(
            index_name=index_name,
            namespace="default",
            embedding=get_embedding_model()
        )
        
    return _vector_store_instance
