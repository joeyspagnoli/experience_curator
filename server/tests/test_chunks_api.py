"""Integration smoke tests for the /chunks/{chunk_id} route."""

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.api import chunks as chunks_api


client = TestClient(app)


def test_get_chunk_returns_row_with_provenance(monkeypatch) -> None:
    """Smoke test: /chunks/{id} returns the chunk joined with its artifact."""
    chunk_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    row = {
        "chunk_id": chunk_id,
        "artifact_id": artifact_id,
        "chunk_index": 0,
        "text": "Built a CI/CD pipeline using GitHub Actions.",
        "locator": {"section": "Projects"},
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "artifact_filename": "ci.md",
        "artifact_path": "storage/artifacts/ci.md",
    }

    def fake_fetch_one(_sql, _params):
        return row

    monkeypatch.setattr(chunks_api, "fetch_one", fake_fetch_one)

    resp = client.get(f"/chunks/{chunk_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["chunk_id"] == str(chunk_id)
    assert body["artifact_id"] == str(artifact_id)
    assert body["chunk_index"] == 0
    assert body["text"] == row["text"]
    assert body["locator"] == {"section": "Projects"}
    assert body["artifact_filename"] == "ci.md"
    assert body["artifact_path"] == "storage/artifacts/ci.md"


def test_get_chunk_returns_404_for_unknown_id(monkeypatch) -> None:
    """Smoke test: /chunks/{id} returns 404 when the chunk does not exist."""
    monkeypatch.setattr(chunks_api, "fetch_one", lambda _sql, _params: None)

    resp = client.get(f"/chunks/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_chunk_returns_400_for_invalid_uuid() -> None:
    """Smoke test: /chunks/{id} rejects malformed chunk ids."""
    resp = client.get("/chunks/not-a-uuid")
    assert resp.status_code == 400
    assert "valid UUID" in resp.json()["detail"]
