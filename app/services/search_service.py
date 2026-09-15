from sqlalchemy.orm import Session

from app.rag.retrieval import semantic_search
from app.repositories import chunk_repository, document_repository


def search_documents(
    db: Session,
    user_id: str,
    query: str,
    document_ids: list[str] | None,
    top_k: int | None,
    score_threshold: float | None,
) -> list[dict]:
    # Validate ownership BEFORE searching — fail loudly on a bad document_id
    # rather than silently returning nothing, which would be confusing to debug.
    if document_ids:
        for doc_id in document_ids:
            if document_repository.get_document_by_id(db, doc_id, user_id) is None:
                raise ValueError(f"Document {doc_id} not found or not owned by you.")

    raw_results = semantic_search(
        query=query,
        user_id=user_id,
        document_ids=document_ids,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    chunk_map = chunk_repository.get_chunks_by_ids(db, [r["chunk_id"] for r in raw_results])

    results = []
    for r in raw_results:
        chunk = chunk_map.get(r["chunk_id"])
        results.append({
            "chunk_id": r["chunk_id"],
            "document_id": r["document_id"],
            "filename": r["filename"],
            "page_number": r["page_number"],
            "score": r["score"],
            "content": chunk.content if chunk else None,
        })
    return results