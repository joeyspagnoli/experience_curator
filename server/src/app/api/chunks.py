"""Chunk lookup routes with artifact provenance."""

import uuid

from fastapi import APIRouter, HTTPException

from ..db_client import fetch_one

router = APIRouter()


def _coerce_chunk_id(raw_chunk_id: str) -> uuid.UUID:
    """Return a UUID parsed from the chunk id path parameter."""
    candidate = raw_chunk_id.strip().strip("'").strip('"')
    try:
        return uuid.UUID(candidate)
    except ValueError:
        try:
            return uuid.UUID(hex=candidate)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="chunk_id must be a valid UUID"
            ) from exc


@router.get(
    "/chunks/{chunk_id}",
    description="Get a chunk with its text, locator, and artifact provenance.",
)
async def get_chunk(chunk_id: str):
    """Return the full chunk row joined with its source artifact."""
    chunk_uuid = _coerce_chunk_id(chunk_id)

    row = fetch_one(
        """
        SELECT
            c.chunk_id,
            c.artifact_id,
            c.chunk_index,
            c.text,
            c.locator,
            c.created_at,
            a.filename AS artifact_filename,
            a.storage_path AS artifact_path
        FROM chunks c
        JOIN artifacts a ON a.id = c.artifact_id
        WHERE c.chunk_id = %s
        """,
        (chunk_uuid,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="chunk not found")
    return row
