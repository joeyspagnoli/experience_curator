import logging

from fastapi import FastAPI, HTTPException, status

from .config import APP_ENV
from .middleware import TraceMiddleware
from .db_client import ping
from .api.folders import router as folders_router
from .api.artifacts import router as artifacts_router
from .api.retrieval import router as retrieval_router
from .api.ask import router as ask_router
from .api.resume_tailor import router as resume_tailor_router
from .api.experience_map import router as experience_map_router
from .api.repo_map import router as repo_map_router
from .api.chunks import router as chunks_router
from .api.runs import router as runs_router

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_middleware(TraceMiddleware)
app.include_router(folders_router)
app.include_router(artifacts_router)
app.include_router(retrieval_router)
app.include_router(ask_router)
app.include_router(resume_tailor_router)
app.include_router(experience_map_router)
app.include_router(repo_map_router)
app.include_router(chunks_router)
app.include_router(runs_router)


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
