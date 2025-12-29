from pathlib import Path
from typing import Any
from docx import Document
from pypdf import PdfReader

MIN_PDF_CHARS: int = 300


class ExtractionError(Exception):
    pass


def extract_txt_or_md(path: Path) -> str:
    """
    Extracts the contents from a .txt or .md file
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ExtractionError(f"Failed to read text file: {path}") from exc


def extract_docx(path: Path) -> str:
    """
    Extracts the contents from a .docx file
    """
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except OSError as exc:
        raise ExtractionError(f"Failed to read docx file: {path}") from exc


def extract_pdf(path: Path) -> tuple[str, dict[str, Any]]:
    """
    Extracts the contents from .pdfs (only if text-pdf)
    """
    try:
        reader = PdfReader(path)
    except OSError as exc:
        raise ExtractionError(f"Failed to read pdf file: {path}") from exc

    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    full_text = "\n".join(pages).strip()
    if len(full_text) < MIN_PDF_CHARS:
        raise ExtractionError("PDF text too short (likely scanned)")
    return full_text, {"page_count": len(pages), "page_texts": pages}


def extract(storage_path: str, filename: str, content_type: str | None):
    """
    Full extraction pipeline for .pdf, .txt, .md, .docx
    """
    path = Path(storage_path)
    if not path.exists():
        raise ExtractionError(f"File not found: {path}")
    ext = Path(filename).suffix.lower()
    _ = content_type  # Reserved for future type-based extraction fallback.

    if ext in {".txt", ".md"}:
        return extract_txt_or_md(path), None
    if ext == ".docx":
        return extract_docx(path), None
    if ext == ".pdf":
        return extract_pdf(path)
    raise ExtractionError(f"Unsupported file type: {ext}")
