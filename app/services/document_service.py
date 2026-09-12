import uuid
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.chunking import chunk_document
from app.rag.ingestion import DocumentProcessingError, extract_document_text, validate_file
from app.repositories import chunk_repository, document_repository
from app.storage.s3_client import delete_object, upload_bytes

settings = get_settings()


async def upload_document(db: Session, user_id: str, file: UploadFile) -> Document:
    content = await file.read()

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

    try:
        upload_bytes(
            document.storage_path,
            content,
            content_type=file.content_type or "application/octet-stream",
        )
        pages = extract_document_text(file_type, content)

        chunks_data = chunk_document(pages, settings.chunk_size, settings.chunk_overlap)
        chunk_rows = [
            DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document.id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                token_count=c["token_count"],
            )
            for c in chunks_data
        ]
        chunk_repository.create_chunks(db, chunk_rows)

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
        pass
    document_repository.delete_document(db, document)
    return True