"""OpenAI-compatible chat completions endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from server.api.auth import require_api_key
from server.core.llama_client import llama_client
from server.rag.retrieval import build_context

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
    use_rag: bool = False


@router.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
async def chat_completions(request: ChatCompletionRequest) -> Any:
    messages = [m.model_dump() for m in request.messages]

    if request.use_rag and messages:
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), None
        )
        if last_user_msg:
            context = await build_context(last_user_msg)
            if context:
                messages = [{"role": "system", "content": context}] + messages

    payload = request.model_dump(exclude_none=True, exclude={"use_rag", "messages"})
    payload["messages"] = messages

    if request.stream:
        return StreamingResponse(
            llama_client.chat_completion_stream(payload),
            media_type="text/event-stream",
        )

    return await llama_client.chat_completion(payload)

