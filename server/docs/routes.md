# Routes v0 — ExperienceCurator.ai

This document lists **implemented** API routes and **placeholder** routes.
No `/api/v1` prefix is used.

## Design approach

- Resource routes mirror schema nouns (folders, artifacts, chunks, runs).
- Workflow routes mirror user journeys (retrieve, ask, resume-tailor).
- Placeholders return 501 until implemented.

---

## Implemented routes

### Health + sanity

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Basic root response for quick sanity checks |
| GET | `/health` | Health check returning current app environment |
| GET | `/db/ping` | Ping DB connection to verify availability |

Response shapes:

```json
// GET /
{ "message": "hello world" }

// GET /health
{ "env": "local" }

// GET /db/ping
{ "ok": true }
```

### Folders

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/folders` | List folders ordered by creation time |
| POST | `/folders` | Create a folder |

Request / response:

```json
// POST /folders
{ "name": "Academics" }

// GET /folders
{
  "items": [
    { "id": "uuid", "name": "Academics", "created_at": "2025-12-26T00:00:00Z" }
  ]
}

// POST /folders
{ "id": "uuid", "name": "Academics", "created_at": "2025-12-26T00:00:00Z" }
```

### Artifacts

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/folders/{folder_id}/artifacts` | List artifacts for a folder |
| POST | `/artifacts/upload` | Upload an artifact and trigger ingestion |
| DELETE | `/artifacts/{artifact_id}` | Delete an artifact |
| GET | `/artifacts/{artifact_id}/chunks` | List chunks for an artifact |

Upload (multipart form):

```
folder_id=<uuid>
file=<UploadFile>
```

Responses:

```json
// GET /folders/{folder_id}/artifacts
{
  "items": [
    {
      "id": "uuid",
      "folder_id": "uuid",
      "filename": "resume.pdf",
      "storage_path": ".../storage/artifacts/uuid__resume.pdf",
      "content_type": "application/pdf",
      "artifact_kind": "doc",
      "ingestion_status": "queued",
      "created_at": "2025-12-26T00:00:00Z"
    }
  ]
}

// POST /artifacts/upload
{
  "id": "uuid",
  "folder_id": "uuid",
  "filename": "resume.pdf",
  "storage_path": ".../storage/artifacts/uuid__resume.pdf",
  "content_type": "application/pdf",
  "artifact_kind": "doc",
  "ingestion_status": "queued",
  "ingestion_stage": "extract",
  "error_message": null,
  "extracted_text_preview": null,
  "file_hash": "sha256",
  "file_size": 12345,
  "chunker_name": null,
  "chunker_params": null,
  "embed_model": null,
  "created_at": "2025-12-26T00:00:00Z"
}

// DELETE /artifacts/{artifact_id}
{ "ok": true }

// GET /artifacts/{artifact_id}/chunks
{
  "items": [
    {
      "chunk_id": "uuid",
      "chunk_index": 0,
      "snippet": "First 500 chars...",
      "locator": { "type": "pdf", "page": 1 },
      "created_at": "2025-12-26T00:00:00Z"
    }
  ]
}
```

### Retrieval

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/retrieve` | Retrieve top-k chunks for a question |

Request:

```json
{
  "question": "Where did I use CI/CD?",
  "scope_folder_ids": ["uuid", "uuid"],
  "top_k": 8
}
```

Response:

```json
{
  "no_evidence": false,
  "results": [
    {
      "chunk_id": "uuid",
      "snippet": "Short preview...",
      "artifact_path": ".../storage/artifacts/uuid__notes.md",
      "score": 0.72
    }
  ]
}
```

Notes:

- `top_k` defaults to 8 (max 50).
- If the top score is below the minimum threshold, the API returns `{ "no_evidence": true, "results": [] }`.

### Ask (Q&A)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/ask` | End-to-end Q&A (retrieve + generate + cite) |

Request:

```json
{
  "question": "Have I used CI/CD?",
  "scope_folder_ids": ["uuid"],
  "citations_mode": "on",
  "top_k": 8
}
```

Response:

```json
{
  "trace_id": "uuid-or-hex",
  "answer_text": "Yes. You used CI in ...",
  "citations": [
    {
      "chunk_id": "uuid",
      "snippet": "Evidence snippet...",
      "artifact_path": ".../storage/artifacts/uuid__notes.md",
      "artifact_filename": "notes.md",
      "score": 0.81,
      "locator": { "type": "md", "heading": "CI/CD", "level": 2 }
    }
  ],
  "retrieved": [
    { "chunk_id": "uuid", "score": 0.81, "rank": 1 }
  ],
  "no_evidence": false,
  "warning": null
}
```

Notes:

- `citations_mode` is `on` or `brainstorm`.
- In `citations_mode=on`, if evidence is weak, the API returns a **no-evidence** answer.

### Runs (debug)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/runs/{trace_id}` | Fetch run metadata, retrieved chunks, and citations |

Response:

```json
{
  "trace_id": "uuid",
  "kind": "ask",
  "created_at": "2025-12-26T00:00:00Z",
  "scope_folder_ids": ["uuid"],
  "question_text": "Have I used CI/CD?",
  "citations_mode": "on",
  "top_k": 8,
  "min_score": 0.25,
  "no_evidence": false,
  "model_name": "gpt-4o-mini",
  "embed_model": "text-embedding-3-small",
  "retrieved": [
    {
      "chunk_id": "uuid",
      "score": 0.81,
      "rank": 1,
      "snippet": "Evidence snippet...",
      "locator": null,
      "artifact_filename": "notes.md",
      "artifact_path": ".../storage/artifacts/uuid__notes.md"
    }
  ],
  "citations": [
    {
      "chunk_id": "uuid",
      "rank": 1,
      "snippet": "Evidence snippet...",
      "locator": null,
      "artifact_filename": "notes.md",
      "artifact_path": ".../storage/artifacts/uuid__notes.md"
    }
  ]
}
```

---

## Placeholder routes (return 501)

These endpoints are wired in FastAPI but intentionally unimplemented.

### Resume Tailor

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/resume-tailor` | Suggest bullet edits grounded in evidence |

### Experience Map

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/experience-map` | List experience map cards |
| POST | `/experience-map/refresh` | Regenerate experience map cards |

### Repo Map

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/repo-map` | Generate a repo map for a code artifact |

### Chunks

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/chunks/{chunk_id}` | Fetch a chunk + artifact provenance |

### Runs

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/runs/{trace_id}/retrieved-chunks` | Placeholder for run retrieved chunks |
