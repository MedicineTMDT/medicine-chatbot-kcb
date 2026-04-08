import json
from db import get_vector_store, vector_store
import os

DIMENSION = 3072 
META_FIELD = "filename" 

vector_store = get_vector_store()
index_name = os.getenv("PINECONE_INDEX_NAME")
index = vector_store.get_pinecone_index(index_name)

with open("files/mapping.json", "r", encoding="utf-8") as f:
    name_map = json.load(f)

count = 0
for old_name, new_name in name_map.items():
    res = index.query(
        vector=[0.0] * DIMENSION, 
        filter={META_FIELD: old_name},
        top_k=10000, 
        include_metadata=False,
        namespace="default"
    )

    print(res)
    for match in res.matches:
        index.update(
            id=match.id, 
            set_metadata={META_FIELD: new_name},
            namespace="default"
        )
        count += 1
        print(f"Updated: {match.id} -> {new_name}")

print(f"Updated {count} records.")
