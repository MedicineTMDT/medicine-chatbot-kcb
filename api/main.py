from fastapi import FastAPI
from api.routers import chat

app = FastAPI(
    title="RAG API System",
    description="API cho hệ thống hỏi đáp RAG",
    version="1.0.0"
)

app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
def health_check():
    return {"status": "OK"}