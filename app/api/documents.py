from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import document_service

from app.repositories import chunk_repository
from app.schemas.document import ChunkOut, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        document = await document_service.upload_document(db, current_user.id, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return document_service.list_documents(db, current_user.id)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = document_service.get_document(db, current_user.id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = document_service.delete_document(db, current_user.id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")



@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = document_service.get_document(db, current_user.id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return chunk_repository.get_chunks_by_document(db, document_id)