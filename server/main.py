"""AnvilLLM API entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from server.api import chat, models, rag
from server.api.logging_middleware import RequestLoggingMiddleware
from server.api.rate_limit import limiter
from server.core.llama_client import llama_client
from server.core.logging_config import setup_logging

_UI_DIR = Path(__file__).parent / "ui"

setup_logging()


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

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "message": "Rate limit exceeded. Please slow down.",
                "type": "rate_limit_error",
            }
        },
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
