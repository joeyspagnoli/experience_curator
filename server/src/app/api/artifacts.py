import uuid
import hashlib
from collections.abc import Mapping
from typing import cast
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.status import HTTP_201_CREATED, HTTP_409_CONFLICT

from ..db_client import execute, fetch_all, fetch_one

router = APIRouter()

ALLOWED_EXTS = {".md", ".txt", ".docx"}
MAX_BYTES = 20 * 1024 * 1024
STORAGE_DIR = Path(__file__).resolve().parents[3] / "storage" / "artifacts"


def _sanitize_filename(filename: str, ext: str) -> str:
    """Create a safe, readable filename segment from user input."""
    stem = Path(filename).stem.lower()
    cleaned = []
    for ch in stem:
        if ch.isalnum():
            cleaned.append(ch)
        elif ch in {" ", "-", "_"}:
            cleaned.append("_")
    safe = "".join(cleaned).strip("_") or "upload"
    safe = safe[:48]
    return f"{safe}{ext}"


def _require_folder_id(folder_id: str) -> uuid.UUID:
    """Parse and validate a folder UUID for artifact uploads."""
    try:
        return uuid.UUID(folder_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="folder_id must be a valid UUID"
        ) from exc


@router.get(
    "/folders/{folder_id}/artifacts",
    description="List all artifacts from a specified folder.",
)
async def get_artifacts(folder_id: str):
    folder_uuid = _require_folder_id(folder_id)
    sql = """
        SELECT id, folder_id, filename, storage_path, content_type, artifact_kind,
               ingestion_status, created_at
        FROM artifacts
        WHERE folder_id = %s
        ORDER BY created_at ASC;
        """
    rows = fetch_all(sql, (folder_uuid,))
    return {"items": rows}


@router.delete(
    "/artifacts/{artifact_id}",
    description="Delete an artifact and remove its stored file.",
)
async def delete_artifact(artifact_id: str):
    try:
        artifact_uuid = uuid.UUID(artifact_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="artifact_id must be a valid UUID"
        ) from exc

    row = fetch_one(
        "SELECT storage_path FROM artifacts WHERE id = %s;",
        (artifact_uuid,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="artifact not found")

    if isinstance(row, Mapping):
        row_map = cast(Mapping[str, object], row)
        storage_path = Path(str(row_map["storage_path"]))
    else:
        storage_path = Path(row[0])
    if storage_path.exists():
        storage_path.unlink()

    execute("DELETE FROM artifacts WHERE id = %s;", (artifact_uuid,))

    return {"ok": True}


@router.post(
    "/artifacts/upload",
    status_code=HTTP_201_CREATED,
    description="Upload a doc, validate type/size, save locally, and create an artifact row in queued status.",
)
async def upload_artifact(
    folder_id: str = Form(...),
    file: UploadFile = File(...),
):
    # Require a filename so we can validate extension and record provenance.
    if not file.filename:
        raise HTTPException(status_code=400, detail="file is required")

    # Validate folder_id format early to avoid bad DB lookups.
    folder_uuid = _require_folder_id(folder_id)

    # Ensure the folder exists before writing the file to disk.
    exists = fetch_one("SELECT id FROM folders WHERE id = %s;", (folder_uuid,))
    if not exists:
        raise HTTPException(status_code=404, detail="folder_id not found")

    # Enforce the allowlist (week 1: md/txt/docx only).
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="unsupported file type")

    # Read the upload into memory to enforce size limits (20MB max).
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="file too large (max 20MB)")

    file_hash = hashlib.sha256(content).hexdigest()
    file_size = len(content)
    duplicate = fetch_one(
        "SELECT id FROM artifacts WHERE folder_id = %s AND file_hash = %s AND file_size = %s;",
        (folder_uuid, file_hash, file_size),
    )
    if duplicate:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="artifact already exists for this folder",
        )

    # Create a safe storage filename (avoid trusting user-supplied name).
    safe_name = _sanitize_filename(file.filename, ext)
    storage_name = f"{uuid.uuid4()}__{safe_name}"
    # Ensure storage directory exists and write the file to disk.
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    storage_path = STORAGE_DIR / storage_name
    storage_path.write_bytes(content)

    # Create a DB row to track this artifact and its ingestion status.
    artifact_id = uuid.uuid4()
    sql = """
        INSERT INTO artifacts (
            id,
            folder_id,
            filename,
            storage_path,
            content_type,
            file_hash,
            file_size,
            artifact_kind,
            ingestion_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    # SQL placeholders (%s) are bound to the tuple below to avoid injection.
    execute(
        sql,
        (
            artifact_id,
            folder_uuid,
            file.filename,
            str(storage_path),
            file.content_type,
            file_hash,
            file_size,
            "doc",
            "queued",
        ),
    )

    # Fetch the inserted row to return a stable response payload.
    row = fetch_one(
        """
        SELECT id, folder_id, filename, storage_path, content_type, artifact_kind,
               ingestion_status, file_hash, file_size, created_at
        FROM artifacts
        WHERE id = %s;
        """,
        (artifact_id,),
    )

    # If we can't read back the row, something went wrong with the insert.
    if not row:
        raise HTTPException(status_code=500, detail="Insert failed unexpectedly")

    return row
