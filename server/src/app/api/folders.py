import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED

from ..db_client import fetch_all, fetch_one


router = APIRouter()


class FolderCreate(BaseModel):
    name: str


def normalize_name(raw: str) -> str:
    """Normalize and validate a folder name before persistence."""
    # Basic folder name rules:
    # - trim leading/trailing whitespace
    # - collapse internal whitespace
    # - no control chars
    # - no path separators
    # TODO: when nested folders exist, validate parent_id and expand retrieval scope to include descendants.
    if any(ch in raw for ch in ["\n", "\r", "\t"]):
        raise HTTPException(status_code=400, detail="name cannot contain control chars")

    name = " ".join(raw.strip().split())

    if len(name) == 0:
        raise HTTPException(status_code=400, detail="name cannot be empty")

    if len(name) > 80:
        raise HTTPException(status_code=400, detail="name must be <= 80 characters")

    if "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="name cannot contain / or \\")

    return name


@router.get(
    "/folders",
    description="List folders ordered by creation time.",
)
async def list_folders():
    sql = "SELECT id, name, created_at FROM folders ORDER BY created_at ASC;"
    rows = fetch_all(sql)
    return {"items": rows}


@router.post(
    "/folders",
    status_code=HTTP_201_CREATED,
    description="Create a folder after normalizing and validating the name.",
)
async def create_folder(payload: FolderCreate):
    name = normalize_name(payload.name)
    folder_id = uuid.uuid4()
    sql = """
        INSERT INTO folders (id, name)
        VALUES (%s, %s)
        RETURNING id, name, created_at
        """
    row = fetch_one(sql, (folder_id, name))

    if not row:
        raise HTTPException(status_code=500, detail="Insert failed unexpectedly")

    return row
