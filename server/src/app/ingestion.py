"""Ingestion pipeline orchestration for artifacts."""

import logging
from collections.abc import Mapping
from typing import Any, cast
import hashlib
import uuid
from psycopg.types.json import Json

from .db_client import execute, execute_many, fetch_one
from .services.extractor import ExtractionError, extract
from .services.chunker import (
    ChunkingError,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    chunk,
)
from .services.embed import EmbeddingError, embed_texts

logger = logging.getLogger(__name__)


def _update_artifact(artifact_id, **fields: Any) -> None:
    """Update artifact columns for a single artifact id."""
    if not fields:
        return
    assignments = ", ".join(f"{key} = %s" for key in fields.keys())
    params = []
    for value in fields.values():
        if isinstance(value, dict):
            params.append(Json(value))
        else:
            params.append(value)
    params.append(artifact_id)
    execute(f"UPDATE artifacts SET {assignments} WHERE id = %s;", params)


def chunk_text(
    text: str,
    *,
    filename: str,
    artifact_kind: str,
    source_meta: dict[str, Any] | None,
):
    """Split extracted text into chunks using the configured chunker."""
    return chunk(
        text,
        filename=filename,
        artifact_kind=artifact_kind,
        source_meta=source_meta,
    )


def embed_chunks(chunks):
    """Embed chunks and persist vectors."""
    if not chunks:
        return {"model_name": None, "model_version": None}
    texts = [chunk["text"] for chunk in chunks]
    embeddings, meta = embed_texts(texts)
    model_name = meta.get("model_name")
    model_version = meta.get("model_version")
    params = []
    for chunked, vector in zip(chunks, embeddings, strict=True):
        params.append(
            (
                chunked["chunk_id"],
                vector,
                model_name,
                model_version,
            )
        )
    execute_many(
        """
        INSERT INTO embeddings (
            chunk_id, embedding, model_name, model_version
        )
        VALUES (%s, %s, %s, %s)
        """,
        params,
    )
    return meta


def _insert_chunks(artifact_id, chunks: list[dict[str, Any]]):
    """Insert chunk rows for an artifact and return the inserted rows."""
    if not chunks:
        return []
    rows = []
    params = []
    for idx, chunk_item in enumerate(chunks):
        chunk_id = uuid.uuid4()
        text = chunk_item["text"]
        locator = chunk_item.get("locator")
        chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rows.append(
            {
                "chunk_id": chunk_id,
                "artifact_id": artifact_id,
                "chunk_index": idx,
                "text": text,
                "locator": locator,
                "chunk_hash": chunk_hash,
            }
        )
        params.append(
            (
                chunk_id,
                artifact_id,
                idx,
                text,
                Json(locator) if locator is not None else None,
                chunk_hash,
            )
        )
    execute_many(
        """
        INSERT INTO chunks (
            chunk_id, artifact_id, chunk_index, text, locator, chunk_hash
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        params,
    )
    return rows


def ingest_artifact(artifact_id) -> None:
    """Run extraction, chunking, and embedding for a single artifact."""
    logger.info("Ingestion started", extra={"artifact_id": str(artifact_id)})
    artifact = fetch_one(
        """
        SELECT id, storage_path, filename, content_type, artifact_kind
        FROM artifacts
        WHERE id = %s;
        """,
        (artifact_id,),
    )
    if not artifact:
        raise RuntimeError("Artifact not found")
    artifact_map = cast(Mapping[str, Any], artifact)

    _update_artifact(
        artifact_id,
        ingestion_status="running",
        ingestion_stage="extract",
        error_message=None,
    )

    try:
        storage_path = str(artifact_map["storage_path"])
        filename = str(artifact_map["filename"])
        content_type = artifact_map["content_type"]
        if content_type is not None:
            content_type = str(content_type)
        logger.info(
            "Extraction started",
            extra={"artifact_id": str(artifact_id), "artifact_filename": filename},
        )
        text, source_meta = extract(storage_path, filename, content_type)
        logger.info(
            "Extraction completed",
            extra={"artifact_id": str(artifact_id), "chars": len(text)},
        )
        preview = text[:500]
        _update_artifact(
            artifact_id,
            ingestion_stage="chunk",
            extracted_text_preview=preview,
        )

        artifact_kind = str(artifact_map["artifact_kind"])
        logger.info(
            "Chunking started",
            extra={"artifact_id": str(artifact_id), "artifact_kind": artifact_kind},
        )
        chunks = chunk_text(
            text,
            filename=filename,
            artifact_kind=artifact_kind,
            source_meta=source_meta,
        )
        logger.info(
            "Chunking completed",
            extra={"artifact_id": str(artifact_id), "chunks": len(chunks)},
        )
        _update_artifact(
            artifact_id,
            chunker_name="hybrid_v0",
            chunker_params={
                "chunk_size": DEFAULT_CHUNK_SIZE,
                "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
                "pdf_mode": "page",
                "md_mode": "heading",
            },
            embed_model="text-embedding-3-small",
        )
        chunk_rows = _insert_chunks(artifact_id, chunks)
        _update_artifact(artifact_id, ingestion_stage="embed")
        logger.info(
            "Embedding started",
            extra={"artifact_id": str(artifact_id), "chunks": len(chunk_rows)},
        )
        embed_meta = embed_chunks(chunk_rows)
        logger.info(
            "Embedding completed",
            extra={
                "artifact_id": str(artifact_id),
                "model": embed_meta.get("model_name"),
            },
        )
        if embed_meta.get("model_name"):
            _update_artifact(
                artifact_id,
                embed_model=embed_meta.get("model_name"),
            )

        _update_artifact(
            artifact_id,
            ingestion_status="succeeded",
            ingestion_stage=None,
        )
        logger.info("Ingestion completed", extra={"artifact_id": str(artifact_id)})
    except ExtractionError as exc:
        logger.exception(
            "Extraction failed",
            extra={"artifact_id": str(artifact_id)},
        )
        _update_artifact(
            artifact_id,
            ingestion_status="failed",
            error_message=str(exc),
        )
    except ChunkingError as exc:
        logger.exception(
            "Chunking failed",
            extra={"artifact_id": str(artifact_id)},
        )
        _update_artifact(
            artifact_id,
            ingestion_status="failed",
            error_message=str(exc),
        )
    except EmbeddingError as exc:
        logger.exception(
            "Embedding failed",
            extra={"artifact_id": str(artifact_id)},
        )
        _update_artifact(
            artifact_id,
            ingestion_status="failed",
            error_message=str(exc),
        )
    except Exception as exc:
        logger.exception(
            "Ingestion failed",
            extra={"artifact_id": str(artifact_id)},
        )
        _update_artifact(
            artifact_id,
            ingestion_status="failed",
            error_message=f"Ingestion failed: {exc}",
        )
