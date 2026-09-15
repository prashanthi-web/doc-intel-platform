from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchAny, MatchValue, PointStruct, VectorParams

from app.config import get_settings

settings = get_settings()

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def ensure_collection_exists(dimension: int) -> None:
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection_name not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )


def upsert_chunks(points: list[dict]) -> None:
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


def search(
    query_vector: list[float],
    user_id: str,
    document_ids: list[str] | None,
    top_k: int,
    score_threshold: float | None,
):
    """Searches Qdrant, always scoped to user_id — the security-critical filter.
    Optionally further scoped to a specific set of document_ids."""
    client = get_qdrant_client()

    must_conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
    if document_ids:
        must_conditions.append(FieldCondition(key="document_id", match=MatchAny(any=document_ids)))

    return client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_vector,
        query_filter=Filter(must=must_conditions),
        limit=top_k,
        score_threshold=score_threshold,
    )