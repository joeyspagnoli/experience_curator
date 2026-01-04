# Server

## How to run locally

- **Entrypoint:** `src/app/main.py` (FastAPI app instance is `app`)
- **Start the server:**
  - `uvicorn src.app.main:app --reload`
- **URLs to hit:**
  - `http://127.0.0.1:8000/health` → JSON with current environment info
  - `http://127.0.0.1:8000/docs` → interactive API docs (Swagger UI)
- **What to expect:**
  - `/health` returns a small JSON payload (e.g., `{"env": "..."}`)
  - `/docs` renders the OpenAPI docs UI when the server is running

## API references

- Route inventory: `server/docs/routes.md`
- Data model: `server/docs/schema_v0.md`

## Upload + ingestion policy (current behavior)

Supported extensions:

- `.md`, `.txt`, `.docx`
- `.pdf` **text-only** (no OCR). PDFs must contain **at least 300 extracted characters**.

If a PDF is scanned or otherwise not text-extractable, extraction fails and ingestion is marked:

- `ingestion_status = failed`
- `error_message = "PDF text too short (likely scanned)"`

Notes:

- The upload allowlist is enforced in `server/src/app/api/artifacts.py`.
- PDF text extraction uses `pypdf` in `server/src/app/services/extractor.py`.

## Ingestion outcomes (documented contract)

Artifacts move through these statuses and stages:

- `ingestion_status`: `queued` → `running` → (`succeeded` | `failed`)
- `ingestion_stage`: `extract` → `chunk` → `embed` (cleared on success)

Failure signals:

- `error_message` is populated on failure (e.g., PDF text too short).
- There is **no structured warning field** in the API today; failure is the only signal.

UI behavior (spec intent):

- When a PDF fails due to low extracted text, the UI should show a **red warning modal**
  that auto-dismisses after **10 seconds**, instructing the user to upload a text-based PDF
  or convert it. (This is not yet implemented in the client.)
