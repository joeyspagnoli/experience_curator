"""Resume Tailor routes (placeholders until workflow is implemented)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class ResumeTailorRequest(BaseModel):
    job_posting: str = Field(..., description="Job posting text to tailor against.")
    resume_artifact_id: str = Field(..., description="Artifact ID for the resume.")


@router.post(
    "/resume-tailor",
    description="Placeholder endpoint for resume bullet tailoring.",
)
async def resume_tailor(_payload: ResumeTailorRequest):
    """Return 501 until resume tailoring is implemented."""
    raise HTTPException(status_code=501, detail="Resume tailor is not implemented yet")
