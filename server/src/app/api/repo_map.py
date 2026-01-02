"""Repo Map routes (placeholders until feature is implemented)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class RepoMapRequest(BaseModel):
    artifact_id: str = Field(..., description="Artifact ID for the repo to map.")


@router.post(
    "/repo-map",
    description="Placeholder endpoint for generating a repo map.",
)
async def repo_map(_payload: RepoMapRequest):
    """Return 501 until repo map is implemented."""
    raise HTTPException(status_code=501, detail="Repo map is not implemented yet")
