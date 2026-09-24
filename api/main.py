from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import require_jwt_auth
from api.routes import chat, conversations, title, completion
from db.postgre.db_store import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="RAG API System",
    description="API cho hệ thống hỏi đáp RAG",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*", # Allow all for dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

protected_route_dependencies = [Depends(require_jwt_auth)]

app.include_router(chat.router, dependencies=protected_route_dependencies)
app.include_router(conversations.router, dependencies=protected_route_dependencies)
app.include_router(title.router, dependencies=protected_route_dependencies)
app.include_router(completion.router, dependencies=protected_route_dependencies)

@app.get("/")
def health_check():
    return {"status": "OK"}
