from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI-Powered Document Intelligence Platform",
    version="0.1.0",
)

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }
