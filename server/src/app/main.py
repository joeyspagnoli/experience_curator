from fastapi import FastAPI
from .config import require, APP_ENV, PORT
from .middleware import TraceMiddleware

app = FastAPI()
app.add_middleware(TraceMiddleware)


@app.get("/")
async def root():
    return {"message": "hello world"}


@app.get("/health")
async def health():
    return {"env": APP_ENV}
