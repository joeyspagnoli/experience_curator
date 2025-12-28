from fastapi import FastAPI, HTTPException, status
from .config import require, APP_ENV, PORT, DATABASE_URL
from .middleware import TraceMiddleware
from .db_client import ping

app = FastAPI()
app.add_middleware(TraceMiddleware)


@app.get("/")
async def root():
    return {"message": "hello world"}


@app.get("/health")
async def health():
    return {"env": APP_ENV}


@app.get("/db/ping")
async def check_db():
    db_pinged = ping()
    if not db_pinged:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database ping failed",
        )
    return {"ok": True}
