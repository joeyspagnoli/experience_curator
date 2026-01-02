import uuid

from app import ingestion


def test_embed_chunks_inserts_embeddings(monkeypatch):
    chunks = [
        {"chunk_id": uuid.uuid4(), "text": "alpha"},
        {"chunk_id": uuid.uuid4(), "text": "beta"},
    ]

    def fake_embed_texts(texts):
        assert texts == ["alpha", "beta"]
        return ([[0.1] * 1536, [0.2] * 1536], {"model_name": "test-model", "model_version": "v1"})

    captured = {}

    def fake_execute_many(sql, params_seq):
        captured["sql"] = sql
        captured["params"] = params_seq
        return len(params_seq)

    monkeypatch.setattr(ingestion, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(ingestion, "execute_many", fake_execute_many)

    meta = ingestion.embed_chunks(chunks)
    assert meta["model_name"] == "test-model"
    assert len(captured["params"]) == 2
    assert captured["params"][0][0] == chunks[0]["chunk_id"]
