from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.config import get_settings
from app.storage.s3_client import ensure_bucket_exists

settings = get_settings()

app = FastAPI(
    title="AI-Powered Document Intelligence Platform",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)


@app.on_event("startup")
def startup_event():
    ensure_bucket_exists()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }