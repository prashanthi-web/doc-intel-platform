import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.rag.ingestion import DocumentProcessingError, extract_document_text, validate_file
from app.repositories import document_repository
from app.storage.s3_client import delete_object, upload_bytes


async def upload_document(db: Session, user_id: str, file: UploadFile) -> Document:
    content = await file.read()

    # Validation failures happen BEFORE we create any DB row or upload anything —
    # a bad upload should leave zero trace.
    try:
        file_type = validate_file(file.filename, content)
    except DocumentProcessingError as e:
        raise ValueError(str(e))

    document = Document(
        id=str(uuid.uuid4()),
        user_id=user_id,
        filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        storage_path="",
        status="pending",
    )
    document.storage_path = f"users/{user_id}/{document.id}/{file.filename}"
    document_repository.create_document(db, document)

    document.status = "processing"
    document_repository.update_document(db, document)

    # From here on, failures are "soft" — the file was valid enough to accept,
    # so we record what went wrong on the row itself instead of rejecting the request.
    try:
        upload_bytes(
            document.storage_path,
            content,
            content_type=file.content_type or "application/octet-stream",
        )
        pages = extract_document_text(file_type, content)

        document.page_count = len(pages) if file_type == "pdf" else None
        document.status = "ready"
        document.processed_at = datetime.now(timezone.utc)
    except DocumentProcessingError as e:
        document.status = "failed"
        document.error_message = str(e)
    except Exception as e:
        document.status = "failed"
        document.error_message = f"Unexpected error: {e}"

    document_repository.update_document(db, document)
    return document


def list_documents(db: Session, user_id: str) -> list[Document]:
    return document_repository.list_documents_by_user(db, user_id)


def get_document(db: Session, user_id: str, document_id: str) -> Document | None:
    return document_repository.get_document_by_id(db, document_id, user_id)


def delete_document(db: Session, user_id: str, document_id: str) -> bool:
    document = document_repository.get_document_by_id(db, document_id, user_id)
    if document is None:
        return False
    try:
        delete_object(document.storage_path)
    except Exception:
        pass  # if it's already gone from S3, still allow removing the DB row
    document_repository.delete_document(db, document)
    return True