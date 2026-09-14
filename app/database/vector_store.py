from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.config import get_settings

settings = get_settings()

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def ensure_collection_exists(dimension: int) -> None:
    """Creates the collection if missing. Safe to call repeatedly."""
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection_name not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )


def upsert_chunks(points: list[dict]) -> None:
    """points: [{"id": str, "vector": list[float], "payload": {...}}, ...]"""
    client = get_qdrant_client()
    client.upsert(
        collection_name=settings.qdrant_collection_name,
        points=[PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"]) for p in points],
    )


def delete_points_by_document(document_id: str) -> None:
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )