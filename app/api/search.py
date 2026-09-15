from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        results = search_service.search_documents(
            db,
            current_user.id,
            payload.query,
            payload.document_ids,
            payload.top_k,
            payload.score_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SearchResponse(query=payload.query, results=results)