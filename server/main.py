"""AnvilLLM API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.api import chat, models
from server.core.llama_client import llama_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await llama_client.close()


app = FastAPI(
    title="AnvilLLM",
    description="Self-hosted, OpenAI-compatible inference API for open-weight models.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(models.router)


@app.get("/")
async def root() -> dict:
    return {"name": "AnvilLLM", "docs": "/docs"}
