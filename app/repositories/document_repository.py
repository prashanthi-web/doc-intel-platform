from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, document: Document) -> Document:
    db.commit()
    db.refresh(document)
    return document


def get_document_by_id(db: Session, document_id: str, user_id: str) -> Document | None:
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def list_documents_by_user(db: Session, user_id: str) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


def delete_document(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()