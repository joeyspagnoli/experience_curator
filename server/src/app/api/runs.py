"""Run trace routes (placeholders until implemented)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get(
    "/runs/{trace_id}",
    description="Placeholder endpoint for fetching a run trace.",
)
async def get_run(_trace_id: str):
    """Return 501 until run lookup is implemented."""
    raise HTTPException(status_code=501, detail="Run lookup is not implemented yet")


@router.get(
    "/runs/{trace_id}/retrieved-chunks",
    description="Placeholder endpoint for fetching retrieved chunks for a run.",
)
async def get_run_retrieved_chunks(_trace_id: str):
    """Return 501 until retrieved chunks lookup is implemented."""
    raise HTTPException(status_code=501, detail="Run retrieved chunks is not implemented yet")
