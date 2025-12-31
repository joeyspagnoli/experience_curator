"""Ask routes (placeholders until Q&A is implemented)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., description="User question to answer.")
    scope_folder_ids: list[str] | None = Field(
        default=None,
        description="Optional list of folder IDs to scope retrieval.",
    )


@router.post(
    "/ask",
    description="Placeholder endpoint for evidence-grounded Q&A.",
)
async def ask(_payload: AskRequest):
    """Return 501 until Q&A is implemented."""
    raise HTTPException(status_code=501, detail="Ask is not implemented yet")
