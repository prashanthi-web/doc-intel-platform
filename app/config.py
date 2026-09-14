from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60

    # --- Database ---
    database_url: str

    # --- Vector DB ---
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "document_chunks"

    # --- Embeddings ---
    embedding_provider: str = "local"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # --- LLM ---
    llm_provider: str = "gemini"
    llm_model_name: str = "gemini-2.0-flash"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None

    # --- RAG ---
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5
    reranking_enabled: bool = False

    # --- Object Storage ---
    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "docintel"
    s3_secret_key: str = "docintel123"
    s3_bucket_name: str = "documents"
    s3_region: str = "us-east-1"


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse .env once, not on every request."""
    return Settings()
