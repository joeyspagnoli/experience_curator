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
