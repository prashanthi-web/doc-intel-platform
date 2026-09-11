import io

import docx
import fitz  # PyMuPDF


class DocumentProcessingError(Exception):
    """Raised when a document fails validation or text can't be extracted from it."""


ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def validate_file(filename: str, content: bytes) -> str:
    """Validates extension, size, and actual file content. Returns the file_type."""
    if "." not in filename:
        raise DocumentProcessingError("File has no extension.")

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentProcessingError(f"Unsupported file type: .{extension}")

    if len(content) == 0:
        raise DocumentProcessingError("File is empty.")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise DocumentProcessingError(
            f"File exceeds max size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    # Magic-byte check: a filename extension can be renamed trivially, so we
    # confirm the actual file content matches what it claims to be.
    if extension == "pdf" and not content.startswith(b"%PDF"):
        raise DocumentProcessingError("File claims to be PDF but its content doesn't match.")
    if extension == "docx" and not content.startswith(b"PK"):
        # DOCX files are zip archives internally; zip files start with "PK".
        raise DocumentProcessingError("File claims to be DOCX but its content doesn't match.")

    return extension


def extract_text_from_pdf(content: bytes) -> list[dict]:
    pages = []
    with fitz.open(stream=content, filetype="pdf") as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            pages.append({"page_number": page_number, "text": text})
    return pages


def extract_text_from_docx(content: bytes) -> list[dict]:
    document = docx.Document(io.BytesIO(content))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    # DOCX has no reliable page boundaries at the file level — Word computes
    # pagination at render time, not stored in the file. We treat it as one page.
    return [{"page_number": None, "text": text.strip()}]


def extract_text_from_txt(content: bytes) -> list[dict]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    return [{"page_number": None, "text": text.strip()}]


def extract_document_text(file_type: str, content: bytes) -> list[dict]:
    extractors = {
        "pdf": extract_text_from_pdf,
        "docx": extract_text_from_docx,
        "txt": extract_text_from_txt,
    }
    pages = extractors[file_type](content)

    non_empty_pages = [p for p in pages if p["text"]]
    if not non_empty_pages:
        raise DocumentProcessingError(
            "No extractable text found — the document may be empty, corrupted, "
            "or a scanned image with no text layer (would need OCR, not yet supported)."
        )

    return pages