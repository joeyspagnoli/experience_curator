"""Unit tests for the /runs/{trace_id} debug route."""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.api import runs as runs_api


client = TestClient(app)


def _patch_fetches(
    monkeypatch,
    *,
    run_row,
    retrieved_rows,
    citation_rows,
) -> None:
    """Stub DB calls for runs endpoint tests."""

    def fake_fetch_one(_sql, _params):
        return run_row

    def fake_fetch_all(_sql, _params):
        if "run_retrieved_chunks" in _sql:
            return retrieved_rows
        if "run_citations" in _sql:
            return citation_rows
        return []

    monkeypatch.setattr(runs_api, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(runs_api, "fetch_all", fake_fetch_all)


def _base_run_row(trace_id: uuid.UUID) -> dict:
    return {
        "trace_id": trace_id,
        "kind": "ask",
        "created_at": "2026-01-01T00:00:00Z",
        "scope_folder_ids": [],
        "question_text": "What is my AI agents experience?",
        "citations_mode": "on",
        "top_k": 8,
        "min_score": 0.25,
        "no_evidence": False,
        "model_name": "gpt-4o-mini",
        "embed_model": "text-embedding-3-small",
    }


def test_runs_happy_path(monkeypatch) -> None:
    """Returns run metadata, retrieved chunks, and citations."""
    trace_id = uuid.uuid4()
    run_row = _base_run_row(trace_id)
    retrieved_rows = [
        {"chunk_id": uuid.uuid4(), "score": 0.5, "rank": 1},
    ]
    citation_rows = [
        {"chunk_id": retrieved_rows[0]["chunk_id"], "rank": 1},
    ]

    _patch_fetches(
        monkeypatch,
        run_row=run_row,
        retrieved_rows=retrieved_rows,
        citation_rows=citation_rows,
    )

    resp = client.get(f"/runs/{trace_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"] == str(trace_id)
    assert body["retrieved"][0]["chunk_id"] == str(retrieved_rows[0]["chunk_id"])
    assert body["retrieved"][0]["score"] == retrieved_rows[0]["score"]
    assert body["retrieved"][0]["rank"] == retrieved_rows[0]["rank"]
    assert body["citations"][0]["chunk_id"] == str(citation_rows[0]["chunk_id"])
    assert body["citations"][0]["rank"] == citation_rows[0]["rank"]


def test_runs_invalid_uuid() -> None:
    """Rejects invalid trace_id."""
    resp = client.get("/runs/not-a-uuid")
    assert resp.status_code == 400


def test_runs_not_found(monkeypatch) -> None:
    """404 when the run is missing."""
    _patch_fetches(
        monkeypatch,
        run_row=None,
        retrieved_rows=[],
        citation_rows=[],
    )
    resp = client.get(f"/runs/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_runs_hex_trace_id(monkeypatch) -> None:
    """Accepts 32-char hex trace_id."""
    trace_id = uuid.uuid4()
    run_row = _base_run_row(trace_id)
    _patch_fetches(
        monkeypatch,
        run_row=run_row,
        retrieved_rows=[],
        citation_rows=[],
    )
    resp = client.get(f"/runs/{trace_id.hex}")
    assert resp.status_code == 200


def test_runs_trace_id_query_fallback(monkeypatch) -> None:
    """Supports Swagger-style {_trace_id} fallback."""
    trace_id = uuid.uuid4()
    run_row = _base_run_row(trace_id)
    _patch_fetches(
        monkeypatch,
        run_row=run_row,
        retrieved_rows=[],
        citation_rows=[],
    )
    resp = client.get(f"/runs/{{trace_id}}?_trace_id={trace_id.hex}")
    assert resp.status_code == 200
