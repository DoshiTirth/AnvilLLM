"""OpenAI-compatible chat completions endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from server.api.auth import require_api_key
from server.core.llama_client import llama_client

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "llama-3.1-8b-instruct"
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


@router.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
async def chat_completions(request: ChatCompletionRequest) -> Any:
    payload = request.model_dump(exclude_none=True)

    if request.stream:
        return StreamingResponse(
            llama_client.chat_completion_stream(payload),
            media_type="text/event-stream",
        )

    return await llama_client.chat_completion(payload)
