import logging
import re
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


class ChunkingError(Exception):
    pass


def _normalize_text(text: str) -> str:
    """Normalize whitespace for stable chunking."""
    # Collapse all whitespace for deterministic chunk boundaries.
    return " ".join(text.split()).strip()


def _split_with_langchain(text: str) -> list[str]:
    """Split text into deterministic chunks using LangChain."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def chunk_pdf_pages(source_meta: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    Chunk PDFs by page using extractor-provided page_texts metadata.
    """
    if not source_meta or "page_texts" not in source_meta:
        raise ChunkingError("Missing PDF page_texts metadata for page chunking")

    chunks: list[dict[str, Any]] = []
    page_texts = source_meta["page_texts"]
    for idx, page_text in enumerate(page_texts):
        normalized = _normalize_text(page_text or "")
        if not normalized:
            continue
        # Split oversized pages while keeping a stable page locator.
        if len(normalized) > DEFAULT_CHUNK_SIZE * 2:
            for part_idx, segment in enumerate(_split_with_langchain(normalized)):
                chunks.append(
                    {
                        "text": segment,
                        "locator": {"type": "pdf", "page": idx + 1, "part": part_idx},
                    }
                )
            continue
        chunks.append({"text": normalized, "locator": {"type": "pdf", "page": idx + 1}})

    if not chunks:
        raise ChunkingError("No chunkable PDF pages found")
    return chunks


def chunk_markdown_headings(text: str) -> list[dict[str, Any]]:
    """
    Chunk markdown by heading boundaries, splitting long sections as needed.
    """
    chunks: list[dict[str, Any]] = []
    current_heading = None
    current_level = None
    current_lines: list[str] = []

    def flush_section() -> None:
        """Emit a chunk (or chunks) for the current heading section."""
        # Join section lines and normalize once to stabilize boundaries.
        if not current_lines:
            return
        section_text = _normalize_text("\n".join(current_lines))
        if not section_text:
            return
        # Split large sections while preserving heading locators.
        segments = (
            _split_with_langchain(section_text)
            if len(section_text) > DEFAULT_CHUNK_SIZE * 2
            else [section_text]
        )
        for part_idx, segment in enumerate(segments):
            chunks.append(
                {
                    "text": segment,
                    "locator": {
                        "type": "md",
                        "heading": current_heading,
                        "level": current_level,
                        "part": part_idx if len(segments) > 1 else None,
                    },
                }
            )

    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.*)", line)
        if match:
            # New heading starts; flush the previous section first.
            flush_section()
            current_heading = match.group(2).strip()
            current_level = len(match.group(1))
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_section()

    if not chunks:
        raise ChunkingError("No markdown chunks produced")
    return chunks


def chunk_text_splitter(text: str) -> list[dict[str, Any]]:
    """
    Chunk free-form text using a size-based splitter.
    """
    normalized = _normalize_text(text)
    if not normalized:
        raise ChunkingError("No text content to chunk")
    segments = _split_with_langchain(normalized)
    return [{"text": segment, "locator": None} for segment in segments]


def chunk_code_placeholder(*_args, **_kwargs):
    """Placeholder for code-aware chunking (not implemented yet)."""
    raise NotImplementedError("Code chunking not implemented yet")


def chunk_summary_placeholder(*_args, **_kwargs):
    """Placeholder for summary/repo-map chunking (not implemented yet)."""
    raise NotImplementedError("Summary chunking not implemented yet")


def chunk(
    text: str,
    *,
    filename: str,
    artifact_kind: str,
    source_meta: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """
    Dispatch chunking strategy based on artifact kind and file extension.
    """
    ext = (filename.rsplit(".", 1)[-1] or "").lower()
    ext = f".{ext}" if ext else ""

    try:
        if artifact_kind == "code":
            return chunk_code_placeholder()
        if artifact_kind in {"repo_map", "resume"}:
            return chunk_summary_placeholder()
        if ext == ".pdf":
            return chunk_pdf_pages(source_meta)
        if ext == ".md":
            return chunk_markdown_headings(text)
        if ext in {".txt", ".docx"}:
            return chunk_text_splitter(text)
    except NotImplementedError:
        raise
    except Exception as exc:
        logger.exception(
            "Chunking failed",
            extra={"artifact_kind": artifact_kind, "ext": ext},
        )
        raise ChunkingError(f"Chunking failed for {artifact_kind}:{ext}") from exc

    raise ChunkingError(f"Unsupported chunking strategy for {artifact_kind}:{ext}")
