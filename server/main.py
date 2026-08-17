"""AnvilLLM API entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from server.api import chat, models, rag
from server.core.llama_client import llama_client

_UI_DIR = Path(__file__).parent / "ui"


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
app.include_router(rag.router)

app.mount("/static", StaticFiles(directory=_UI_DIR / "static"), name="static")
_templates = Jinja2Templates(directory=_UI_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def web_ui(request: Request) -> HTMLResponse:
    return _templates.TemplateResponse(request, "index.html", {})


@app.get("/api")
async def api_info() -> dict:
    return {"name": "AnvilLLM", "docs": "/docs"}
