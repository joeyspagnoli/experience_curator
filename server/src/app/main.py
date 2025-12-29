import logging

from fastapi import FastAPI, HTTPException, status

from .config import APP_ENV
from .middleware import TraceMiddleware
from .db_client import ping
from .api.folders import router as folders_router
from .api.artifacts import router as artifacts_router

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_middleware(TraceMiddleware)
app.include_router(folders_router)
app.include_router(artifacts_router)


@app.get("/", description="Basic root response for quick sanity checks.")
async def root():
    return {"message": "hello world"}


@app.get("/health", description="Health check returning the current app environment.")
async def health():
    return {"env": APP_ENV}


@app.get("/db/ping", description="Ping the database connection to verify availability.")
async def check_db():
    db_pinged = ping()
    if not db_pinged:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database ping failed",
        )
    return {"ok": True}


@app.get(
    "/debug/search",
    description="Placeholder endpoint for vector search debugging.",
)
async def debug_search(q: str, k: int = 5):
    """Embed the query, run vector search, and return top-k chunks with scores."""
    _ = q
    _ = k
    raise NotImplementedError("Debug search is not implemented yet")
