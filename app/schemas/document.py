from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: str | None = None
    page_count: int | None = None
    uploaded_at: datetime
    processed_at: datetime | None = None

    class Config:
        from_attributes = True
        
class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    page_number: int | None
    content: str
    token_count: int
    is_embedded: bool

    class Config:
        from_attributes = True