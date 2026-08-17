# RAG (Retrieval-Augmented Generation)

AnvilLLM's base model (Llama 3.1 8B) has a frozen training cutoff of
December 2023. The RAG layer works around this by injecting relevant context
into the prompt at query time - from your own documents, live web search,
or both. This never involves calling another LLM's API; the fetched context
is just additional text handed to the local model, the same as any other
tool-use result.

## Enabling RAG

Set in your `.env`:

```
ENABLE_RAG=true
VECTOR_STORE_PATH=./data/vectorstore

# Optional - only needed if you want live web search retrieval too
WEB_SEARCH_PROVIDER=brave        # or "serper"
WEB_SEARCH_API_KEY=your-key-here
```

Local document retrieval works with no additional setup or API key -
`WEB_SEARCH_*` is only needed for the live search component.

> **Note:** on first use, the local vector store downloads a small
> (~90MB) embedding model over the network - a one-time setup step,
> similar to the Llama model weights download. After that, embedding
> happens entirely on-device.

## Ingesting your own documents

```bash
curl http://localhost:8080/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Your document content here...", "source": "my-notes"}'
```

Text is automatically chunked before being embedded and stored.

## Using RAG in chat requests

Add `"use_rag": true` to any `/v1/chat/completions` request:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What does our ingested doc say about X?"}],
    "use_rag": true
  }'
```

When enabled, the last user message is used as the retrieval query; matching
local document chunks and (if configured) web search results are injected
as a system message ahead of the conversation.

## Testing retrieval directly

```bash
curl http://localhost:8080/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here", "top_k": 4}'
```

Returns the raw context block that would be injected, without running it
through the model - useful for debugging what's actually being retrieved.

## Web search providers

Currently supported: **Brave Search API** and **Serper** (Google search
wrapper). Both require their own API key from the respective provider - get
one and set `WEB_SEARCH_PROVIDER` + `WEB_SEARCH_API_KEY` accordingly. If
unset, RAG still works using local documents only.
