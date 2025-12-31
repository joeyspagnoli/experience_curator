"""Integration smoke tests for the /retrieve route."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import retrieval as retrieval_api


# Reuse a single TestClient to exercise the FastAPI route.
client = TestClient(app)


def test_retrieve_returns_results(monkeypatch) -> None:
    """Smoke test: /retrieve returns rows when evidence is strong enough."""
    chunk_id = uuid.uuid4()
    rows = [
        {
            "chunk_id": chunk_id,
            "snippet": "CI/CD pipeline setup and deployment notes.",
            "artifact_path": "storage/artifacts/example.md",
            "score": 0.42,
        }
    ]

    def fake_embed_texts(texts):
        # Avoid network calls by returning a deterministic embedding.
        assert texts == ["CI/CD"]
        return ([[0.1, 0.2, 0.3]], {"model_name": "test-model", "model_version": "v1"})

    def fake_fetch_all(sql, params):
        # Basic sanity checks that the SQL is the retrieval query.
        assert "FROM embeddings" in sql
        assert params[0] == retrieval_api.DEFAULT_SNIPPET_LEN
        assert params[-1] == retrieval_api.DEFAULT_TOP_K
        return rows

    # Patch the embed + DB helpers used by the route.
    monkeypatch.setattr(retrieval_api, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(retrieval_api, "fetch_all", fake_fetch_all)

    resp = client.post("/retrieve", json={"question": "CI/CD", "top_k": 8})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is False
    assert body["results"][0]["chunk_id"] == str(chunk_id)
    assert body["results"][0]["score"] == pytest.approx(0.42)


def test_retrieve_returns_no_evidence_when_score_is_low(monkeypatch) -> None:
    """Smoke test: /retrieve returns no_evidence when top score is below threshold."""
    rows = [
        {
            "chunk_id": uuid.uuid4(),
            "snippet": "Unrelated content.",
            "artifact_path": "storage/artifacts/unrelated.md",
            "score": retrieval_api.DEFAULT_MIN_SCORE - 0.01,
        }
    ]

    def fake_embed_texts(_texts):
        # Return any embedding; the score threshold is tested via fake rows.
        return ([[0.0, 0.0, 1.0]], {"model_name": "test-model", "model_version": "v1"})

    def fake_fetch_all(_sql, _params):
        return rows

    monkeypatch.setattr(retrieval_api, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(retrieval_api, "fetch_all", fake_fetch_all)

    resp = client.post("/retrieve", json={"question": "CI/CD"})
    assert resp.status_code == 200
    assert resp.json() == {"no_evidence": True, "results": []}
