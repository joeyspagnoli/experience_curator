"""Unit tests for artifact routes and helpers."""
import io
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api import artifacts as artifacts_api


client = TestClient(app)


def test_sanitize_filename_basic():
    """Sanitize should lower-case, replace spaces, and keep extension."""
    assert artifacts_api._sanitize_filename("My File Name.md", ".md") == "my_file_name.md"


def test_sanitize_filename_fallback():
    """Sanitize should fall back to 'upload' when name is empty after cleaning."""
    assert artifacts_api._sanitize_filename("!!!", ".txt") == "upload.txt"


def test_require_folder_id_invalid():
    """Invalid UUID should raise a 400 HTTPException."""
    with pytest.raises(HTTPException):
        artifacts_api._require_folder_id("not-a-uuid")


def test_get_artifacts_invalid_uuid():
    """GET artifacts with invalid folder_id returns 400."""
    resp = client.get("/folders/not-a-uuid/artifacts")
    assert resp.status_code == 400


def test_get_artifacts_success(monkeypatch):
    """GET artifacts returns rows from fetch_all."""
    folder_id = str(uuid.uuid4())
    rows = [{"id": str(uuid.uuid4()), "folder_id": folder_id, "filename": "a.md"}]

    def fake_fetch_all(sql, params=None):
        return rows

    monkeypatch.setattr(artifacts_api, "fetch_all", fake_fetch_all)
    resp = client.get(f"/folders/{folder_id}/artifacts")
    assert resp.status_code == 200
    assert resp.json() == {"items": rows}


def test_upload_invalid_folder_id():
    """Upload rejects invalid folder_id before any DB work."""
    file_bytes = io.BytesIO(b"hello")
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": "bad-id"},
        files={"file": ("note.md", file_bytes, "text/markdown")},
    )
    assert resp.status_code == 400


def test_upload_folder_not_found(monkeypatch):
    """Upload returns 404 when folder lookup fails."""
    def fake_fetch_one(sql, params=None):
        if "FROM folders" in sql:
            return None
        return None

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    file_bytes = io.BytesIO(b"hello")
    folder_id = str(uuid.uuid4())
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": folder_id},
        files={"file": ("note.md", file_bytes, "text/markdown")},
    )
    assert resp.status_code == 404


def test_upload_unsupported_extension(monkeypatch):
    """Upload rejects unsupported extensions."""
    def fake_fetch_one(sql, params=None):
        if "FROM folders" in sql:
            return {"id": params[0]}
        return None

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    file_bytes = io.BytesIO(b"hello")
    folder_id = str(uuid.uuid4())
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": folder_id},
        files={"file": ("note.pdf", file_bytes, "application/pdf")},
    )
    assert resp.status_code == 400


def test_upload_too_large(monkeypatch):
    """Upload rejects files larger than MAX_BYTES."""
    def fake_fetch_one(sql, params=None):
        if "FROM folders" in sql:
            return {"id": params[0]}
        return None

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(artifacts_api, "MAX_BYTES", 1)
    file_bytes = io.BytesIO(b"too-large")
    folder_id = str(uuid.uuid4())
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": folder_id},
        files={"file": ("note.md", file_bytes, "text/markdown")},
    )
    assert resp.status_code == 400


def test_upload_duplicate(monkeypatch):
    """Upload returns 409 when a duplicate artifact exists in the folder."""
    def fake_fetch_one(sql, params=None):
        if "FROM folders" in sql:
            return {"id": params[0]}
        if "file_hash" in sql:
            return {"id": str(uuid.uuid4())}
        return None

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    file_bytes = io.BytesIO(b"hello")
    folder_id = str(uuid.uuid4())
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": folder_id},
        files={"file": ("note.md", file_bytes, "text/markdown")},
    )
    assert resp.status_code == 409


def test_upload_success_saves_and_returns_row(monkeypatch, tmp_path):
    """Upload success writes file, inserts row, and returns artifact data."""
    captured = {}

    def fake_execute(sql, params=None):
        captured["artifact_id"] = params[0]
        captured["storage_path"] = params[3]
        captured["file_hash"] = params[5]
        captured["file_size"] = params[6]

    def fake_fetch_one(sql, params=None):
        if "FROM folders" in sql:
            return {"id": params[0]}
        if "WHERE id = %s" in sql:
            return {
                "id": str(captured["artifact_id"]),
                "folder_id": str(params[0]),
                "filename": "note.md",
                "storage_path": captured["storage_path"],
                "content_type": "text/markdown",
                "artifact_kind": "doc",
                "ingestion_status": "queued",
                "file_hash": captured["file_hash"],
                "file_size": captured["file_size"],
                "created_at": "2025-01-01T00:00:00Z",
            }
        if "file_hash" in sql:
            return None
        return None

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(artifacts_api, "execute", fake_execute)
    monkeypatch.setattr(artifacts_api, "STORAGE_DIR", tmp_path)

    file_bytes = io.BytesIO(b"hello")
    folder_id = str(uuid.uuid4())
    resp = client.post(
        "/artifacts/upload",
        data={"folder_id": folder_id},
        files={"file": ("note.md", file_bytes, "text/markdown")},
    )
    assert resp.status_code == 201
    assert any(tmp_path.iterdir())


def test_delete_artifact_removes_file(monkeypatch, tmp_path):
    """Delete removes file and calls execute for DB delete."""
    artifact_id = str(uuid.uuid4())
    test_file = tmp_path / "file.md"
    test_file.write_text("data")

    def fake_fetch_one(sql, params=None):
        return {"storage_path": str(test_file)}

    captured = {}

    def fake_execute(sql, params=None):
        captured["params"] = params

    monkeypatch.setattr(artifacts_api, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(artifacts_api, "execute", fake_execute)

    resp = client.delete(f"/artifacts/{artifact_id}")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert not test_file.exists()
    assert captured["params"][0] == uuid.UUID(artifact_id)
