from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


def create_chunks(db: Session, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    db.add_all(chunks)
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return chunks


def get_chunks_by_document(db: Session, document_id: str) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

def get_chunks_by_ids(db: Session, chunk_ids: list[str]) -> dict[str, DocumentChunk]:
    if not chunk_ids:
        return {}
    chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
    return {c.id: c for c in chunks}