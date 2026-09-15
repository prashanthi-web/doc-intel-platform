from app.config import get_settings
from app.database.vector_store import search as qdrant_search
from app.rag.embeddings import get_embedding_provider

settings = get_settings()


def semantic_search(
    query: str,
    user_id: str,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[dict]:
    """Embeds the query with the SAME provider used to embed documents, searches
    Qdrant, and returns ranked results with citation metadata. Does NOT include
    full chunk text — that's fetched from MySQL afterward (source of truth)."""
    provider = get_embedding_provider()
    query_vector = provider.embed_query(query)

    k = top_k if top_k is not None else settings.retrieval_top_k
    threshold = score_threshold if score_threshold is not None else settings.similarity_score_threshold

    hits = qdrant_search(
        query_vector=query_vector,
        user_id=user_id,
        document_ids=document_ids,
        top_k=k,
        score_threshold=threshold,
    )

    return [
        {
            "chunk_id": hit.id,
            "score": hit.score,
            "document_id": hit.payload["document_id"],
            "filename": hit.payload["filename"],
            "page_number": hit.payload.get("page_number"),
        }
        for hit in hits
    ]