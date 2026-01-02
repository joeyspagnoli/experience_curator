"""Unit tests for folder routes and helpers."""
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.api import folders as folders_api


# Test client for route-level assertions.
client = TestClient(app)


def test_normalize_name_trims_and_collapses():
    """Normalize trims edges and collapses internal whitespace."""
    assert folders_api.normalize_name("  Work   Projects ") == "Work Projects"


def test_normalize_name_rejects_empty():
    """Normalize rejects empty or whitespace-only names."""
    with pytest.raises(HTTPException):
        folders_api.normalize_name("   ")


def test_normalize_name_rejects_long():
    """Normalize rejects names longer than the max length."""
    with pytest.raises(HTTPException):
        folders_api.normalize_name("a" * 81)


def test_normalize_name_rejects_control_chars():
    """Normalize rejects control characters such as newlines."""
    with pytest.raises(HTTPException):
        folders_api.normalize_name("hello\nworld")


def test_normalize_name_rejects_path_separators():
    """Normalize rejects slash characters used in paths."""
    with pytest.raises(HTTPException):
        folders_api.normalize_name("bad/name")


def test_list_folders_returns_items(monkeypatch):
    """GET /folders returns the rows from fetch_all."""
    rows = [
        {"id": str(uuid.uuid4()), "name": "Work", "created_at": "2025-01-01T00:00:00Z"},
        {"id": str(uuid.uuid4()), "name": "Projects", "created_at": "2025-01-02T00:00:00Z"},
    ]

    def fake_fetch_all(sql, params=None):
        return rows

    monkeypatch.setattr(folders_api, "fetch_all", fake_fetch_all)
    resp = client.get("/folders")
    assert resp.status_code == 200
    assert resp.json() == {"items": rows}


def test_create_folder_normalizes_and_returns_row(monkeypatch):
    """POST /folders normalizes the name and returns the created row."""
    captured = {}

    def fake_fetch_one(sql, params=None):
        assert params is not None
        captured["params"] = params
        return {"id": str(params[0]), "name": params[1], "created_at": "2025-01-01T00:00:00Z"}

    monkeypatch.setattr(folders_api, "fetch_one", fake_fetch_one)
    resp = client.post("/folders", json={"name": "  Work   Projects "})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Work Projects"
    assert captured["params"][1] == "Work Projects"


def test_create_folder_insert_failure(monkeypatch):
    """POST /folders returns 500 when insert returns no row."""
    def fake_fetch_one(sql, params=None):
        return None

    monkeypatch.setattr(folders_api, "fetch_one", fake_fetch_one)
    resp = client.post("/folders", json={"name": "Work"})
    assert resp.status_code == 500
