from vector_db import get_vector_store

vector_store = get_vector_store()
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

docs = retriever.invoke("Phần tài liệu tham khảo của phác đồ điều trị bệnh tả bao gồm những gi?")

print(f"Số lượng chunk tìm được: {len(docs)}")
for i, doc in enumerate(docs):
    print(f"--- Chunk {i+1} ---")
    print(doc.page_content)

# from pinecone.grpc import PineconeGRPC as Pinecone
# import os
# from dotenv import load_dotenv

# load_dotenv()

# PINECONE_API_KEY =os.getenv("PINECONE_API_KEY")
# pc = Pinecone(api_key=PINECONE_API_KEY)

# index_list = pc.list_indexes()

# print(index_list)