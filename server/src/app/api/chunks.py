"""Chunk lookup routes (placeholders until implemented)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get(
    "/chunks/{chunk_id}",
    description="Placeholder endpoint for fetching a chunk with provenance.",
)
async def get_chunk(_chunk_id: str):
    """Return 501 until chunk lookup is implemented."""
    raise HTTPException(status_code=501, detail="Chunk lookup is not implemented yet")
