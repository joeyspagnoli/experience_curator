"""Experience Map routes (placeholders until feature is implemented)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get(
    "/experience-map",
    description="Placeholder endpoint for listing experience map cards.",
)
async def list_experience_map():
    """Return 501 until experience map is implemented."""
    raise HTTPException(status_code=501, detail="Experience map is not implemented yet")


@router.post(
    "/experience-map/refresh",
    description="Placeholder endpoint for regenerating experience map cards.",
)
async def refresh_experience_map():
    """Return 501 until experience map refresh is implemented."""
    raise HTTPException(status_code=501, detail="Experience map refresh is not implemented yet")
