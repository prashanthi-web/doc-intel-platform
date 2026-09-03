from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI-Powered Document Intelligence Platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Basic liveness check + confirms env config loaded correctly."""
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }

