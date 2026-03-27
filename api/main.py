from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from api.routers import chat, conversations


app = FastAPI(
    title="RAG API System",
    description="API cho hệ thống hỏi đáp RAG",
    version="1.0.0"
)

app.include_router(chat.router)
app.include_router(conversations.router)

@app.get("/")
def health_check():
    return {"status": "OK"}