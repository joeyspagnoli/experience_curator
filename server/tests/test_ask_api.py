"""Integration smoke tests for the /ask route."""

import json
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.api import ask as ask_api


client = TestClient(app)


def _patch_common(monkeypatch) -> None:
    """Patch shared dependencies for /ask tests to avoid network and DB calls."""

    def fake_embed_texts(texts):
        assert texts
        return ([[0.1, 0.2, 0.3]], {"model_name": "test-embed", "model_version": "v1"})

    monkeypatch.setattr(ask_api, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(ask_api, "_record_run", lambda **_kwargs: None)
    monkeypatch.setattr(ask_api, "_record_citations", lambda **_kwargs: None)


def test_ask_returns_no_evidence_when_empty(monkeypatch) -> None:
    """Smoke test: /ask returns no_evidence when retrieval is empty."""
    _patch_common(monkeypatch)

    def fake_fetch_all(_sql, _params):
        return []

    monkeypatch.setattr(ask_api, "fetch_all", fake_fetch_all)

    resp = client.post("/ask", json={"question": "CI/CD"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is True
    assert body["citations"] == []
    assert body["retrieved"] == []


def test_ask_returns_answer_with_citations(monkeypatch) -> None:
    """Smoke test: /ask returns answer and citations when evidence exists."""
    _patch_common(monkeypatch)

    chunk_id = uuid.uuid4()
    rows = [
        {
            "chunk_id": chunk_id,
            "snippet": "Built a CI/CD pipeline using GitHub Actions.",
            "artifact_path": "storage/artifacts/ci.md",
            "artifact_filename": "ci.md",
            "score": 0.42,
            "locator": None,
        }
    ]

    def fake_fetch_all(_sql, _params):
        return rows

    def fake_call_chat(_messages):
        payload = {"answer": "Yes, you used CI/CD.", "citations": [str(chunk_id)]}
        return json.dumps(payload)

    monkeypatch.setattr(ask_api, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(ask_api, "_call_chat", fake_call_chat)

    resp = client.post("/ask", json={"question": "Have I used CI/CD?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is False
    assert body["answer_text"] == "Yes, you used CI/CD."
    assert body["citations"][0]["chunk_id"] == str(chunk_id)
    assert body["retrieved"][0]["chunk_id"] == str(chunk_id)
    assert body["retrieved"][0]["rank"] == 1


def test_ask_returns_no_evidence_on_invalid_citation(monkeypatch) -> None:
    """Smoke test: /ask refuses when model cites unknown chunk ids."""
    _patch_common(monkeypatch)

    rows = [
        {
            "chunk_id": uuid.uuid4(),
            "snippet": "Unrelated chunk text.",
            "artifact_path": "storage/artifacts/unrelated.md",
            "artifact_filename": "unrelated.md",
            "score": 0.5,
            "locator": None,
        }
    ]

    def fake_fetch_all(_sql, _params):
        return rows

    def fake_call_chat(_messages):
        payload = {"answer": "Yes, definitely.", "citations": ["not-a-real-id"]}
        return json.dumps(payload)

    monkeypatch.setattr(ask_api, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(ask_api, "_call_chat", fake_call_chat)

    resp = client.post("/ask", json={"question": "Have I used CI/CD?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is True
    assert body["answer_text"] == ask_api.NO_EVIDENCE_MESSAGE


def test_ask_brainstorm_returns_warning(monkeypatch) -> None:
    """Smoke test: brainstorm mode returns a warning and allows empty evidence."""
    _patch_common(monkeypatch)

    def fake_fetch_all(_sql, _params):
        return []

    def fake_call_chat(_messages):
        payload = {"answer": "Possibly, if you used Linux in past roles.", "citations": []}
        return json.dumps(payload)

    monkeypatch.setattr(ask_api, "fetch_all", fake_fetch_all)
    monkeypatch.setattr(ask_api, "_call_chat", fake_call_chat)

    resp = client.post(
        "/ask",
        json={"question": "What's my Linux experience?", "citations_mode": "brainstorm"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["warning"]
    assert body["answer_text"]
