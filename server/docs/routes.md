# Routes v0 — ExperienceCurator.ai

This document lists the current API routes and the foundation routes implied by
the product spec and schema (`server/docs/schema_v0.md`). No `/api/v1` prefix is
used.

## Design approach

- Resource routes mirror schema nouns (folders, artifacts, chunks, runs).
- Workflow routes mirror user journeys (retrieve, ask, resume-tailor).
- Placeholders exist for planned features; they return 501 until implemented.

## Current routes (implemented)

### Folders

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/folders` | List folders ordered by creation time |
| POST | `/folders` | Create a folder |

### Artifacts

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/folders/{folder_id}/artifacts` | List artifacts for a folder |
| POST | `/artifacts/upload` | Upload an artifact and trigger ingestion |
| DELETE | `/artifacts/{artifact_id}` | Delete an artifact |

## Foundation routes (placeholders)

### Retrieval + Q&A

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/retrieve` | Retrieve top-k chunks for a question |
| POST | `/ask` | End-to-end Q&A (retrieve + generate + cite) |

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

### Chunks (citation lookup)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/chunks/{chunk_id}` | Fetch a chunk + artifact provenance |

### Runs (debug trace)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/runs/{trace_id}` | Fetch run metadata |
| GET | `/runs/{trace_id}/retrieved-chunks` | Fetch retrieved chunks for a run |

## Notes

- The spec prefers `/folders/{folder_id}/artifacts` for uploads, but the current
  implementation uses `/artifacts/upload`. We can add the nested POST later.
- Placeholders should be implemented in small increments to avoid large rewrites.
