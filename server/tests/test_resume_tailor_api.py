"""Integration smoke tests for the /resume-tailor route."""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.api import ask as ask_api
from app.api import resume_tailor as resume_tailor_api


client = TestClient(app)


def _patch_common(monkeypatch) -> None:
    """Patch shared dependencies for /resume-tailor tests to avoid network and DB calls."""

    def fake_embed_texts(texts):
        assert texts
        return ([[0.1, 0.2, 0.3]], {"model_name": "test-embed", "model_version": "v1"})

    # _retrieve_chunks lives in ask_api, so embed/fetch resolve there.
    monkeypatch.setattr(ask_api, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(resume_tailor_api, "_record_run", lambda **_kwargs: None)
    monkeypatch.setattr(resume_tailor_api, "_record_citations", lambda **_kwargs: None)


def _make_rows(count: int) -> list[dict]:
    return [
        {
            "chunk_id": uuid.uuid4(),
            "snippet": f"Evidence snippet {index}.",
            "artifact_path": f"storage/artifacts/evidence-{index}.md",
            "artifact_filename": f"evidence-{index}.md",
            "score": 0.5 - index * 0.05,
            "locator": None,
        }
        for index in range(count)
    ]


def test_resume_tailor_rejects_empty_job_description(monkeypatch) -> None:
    """Smoke test: /resume-tailor returns 400 for a whitespace job description."""
    _patch_common(monkeypatch)

    resp = client.post("/resume-tailor", json={"job_description": "   "})
    assert resp.status_code == 400


def test_resume_tailor_returns_no_evidence_when_empty(monkeypatch) -> None:
    """Smoke test: /resume-tailor returns no_evidence when retrieval is empty."""
    _patch_common(monkeypatch)
    monkeypatch.setattr(ask_api, "fetch_all", lambda _sql, _params: [])

    resp = client.post("/resume-tailor", json={"job_description": "Backend engineer role"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is True
    assert body["suggestions"] == []
    assert body["evidence"] == []
    assert body["message"] == resume_tailor_api.NO_EVIDENCE_MESSAGE


def test_resume_tailor_returns_cited_suggestions(monkeypatch) -> None:
    """Smoke test: /resume-tailor returns suggestions with resolved citations."""
    _patch_common(monkeypatch)

    rows = _make_rows(2)
    cited_id = str(rows[0]["chunk_id"])
    monkeypatch.setattr(ask_api, "fetch_all", lambda _sql, _params: rows)

    draft = resume_tailor_api.ResumeTailorDraft(
        suggestions=[
            resume_tailor_api.SuggestionDraft(
                bullet="Built a CI/CD pipeline with GitHub Actions.",
                rationale="The posting asks for CI/CD experience.",
                citation_chunk_ids=[cited_id],
            )
        ]
    )
    monkeypatch.setattr(
        resume_tailor_api, "_generate_suggestions", lambda _jd, _rows: draft
    )

    resp = client.post("/resume-tailor", json={"job_description": "CI/CD heavy role"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is False
    assert len(body["suggestions"]) == 1
    suggestion = body["suggestions"][0]
    assert suggestion["bullet"] == "Built a CI/CD pipeline with GitHub Actions."
    assert suggestion["citations"][0]["chunk_id"] == cited_id
    assert len(body["evidence"]) == 2


def test_resume_tailor_drops_suggestion_with_unknown_citation(monkeypatch) -> None:
    """Smoke test: a suggestion citing an unknown chunk id falls back to no_evidence."""
    _patch_common(monkeypatch)

    rows = _make_rows(1)
    monkeypatch.setattr(ask_api, "fetch_all", lambda _sql, _params: rows)

    draft = resume_tailor_api.ResumeTailorDraft(
        suggestions=[
            resume_tailor_api.SuggestionDraft(
                bullet="Shipped a Kubernetes migration.",
                rationale="The posting mentions Kubernetes.",
                citation_chunk_ids=["not-a-real-id"],
            )
        ]
    )
    monkeypatch.setattr(
        resume_tailor_api, "_generate_suggestions", lambda _jd, _rows: draft
    )

    resp = client.post("/resume-tailor", json={"job_description": "Kubernetes role"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is True
    assert body["suggestions"] == []
    assert body["message"] == resume_tailor_api.NO_EVIDENCE_MESSAGE


def test_resume_tailor_keeps_only_valid_suggestions(monkeypatch) -> None:
    """Smoke test: mixed drafts keep the validly cited suggestion and drop the rest."""
    _patch_common(monkeypatch)

    rows = _make_rows(2)
    valid_id = str(rows[1]["chunk_id"])
    monkeypatch.setattr(ask_api, "fetch_all", lambda _sql, _params: rows)

    draft = resume_tailor_api.ResumeTailorDraft(
        suggestions=[
            resume_tailor_api.SuggestionDraft(
                bullet="Invented a metric with no support.",
                rationale="Not grounded.",
                citation_chunk_ids=["not-a-real-id"],
            ),
            resume_tailor_api.SuggestionDraft(
                bullet="Automated deploys with GitHub Actions.",
                rationale="Matches the posting's automation focus.",
                citation_chunk_ids=[valid_id],
            ),
        ]
    )
    monkeypatch.setattr(
        resume_tailor_api, "_generate_suggestions", lambda _jd, _rows: draft
    )

    resp = client.post("/resume-tailor", json={"job_description": "Automation role"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["no_evidence"] is False
    assert len(body["suggestions"]) == 1
    assert body["suggestions"][0]["bullet"] == "Automated deploys with GitHub Actions."
    assert body["suggestions"][0]["citations"][0]["chunk_id"] == valid_id
