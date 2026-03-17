from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import chat

# Khởi tạo App FastAPI
app = FastAPI(
    title="Production RAG API",
    description="Hệ thống API kết hợp FastAPI, LangChain, Pinecone và OpenAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các router vào app
app.include_router(chat.router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "RAG System is running smoothly!"}

if __name__ == "__main__":
    import uvicorn
    # Chạy server ở port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)