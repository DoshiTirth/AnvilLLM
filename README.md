<p align="center">
  <img src="docs/logo.svg" width="120" alt="AnvilLLM logo">
</p>

<h1 align="center">AnvilLLM</h1>
<p align="center"><i>Self-hosted, OpenAI-compatible inference for open-weight models</i></p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/model-Llama%203.1%208B-informational" alt="Llama 3.1 8B">
  <img src="https://img.shields.io/badge/status-work%20in%20progress-yellow" alt="WIP">
</p>

---

## What is AnvilLLM?

AnvilLLM is a self-hosted inference stack for open-weight LLMs. It wraps
[llama.cpp](https://github.com/ggerganov/llama.cpp) running Llama 3.1 8B
(GGUF, quantized) behind:

- An **OpenAI-compatible REST API** — drop-in for existing `/v1/chat/completions` clients
- A **lightweight web UI** for chatting with the model directly
- An optional **RAG layer** (local documents + web search retrieval) to work around the model's frozen training-data cutoff

Everything runs on your own hardware. No prompts, responses, or data are ever sent to a third-party LLM API — the reasoning happens entirely on the local model.

> Status: scaffolding in progress. This README will be filled in with real
> screenshots, architecture diagrams, and usage examples as each part lands.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────────┐
│  Web UI /   │◄────►│  FastAPI     │◄────►│  llama-server     │
│  API client │      │  (this repo) │      │  (llama.cpp)      │
└─────────────┘      └──────┬───────┘      └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  RAG layer        │
                    │  (local vectors + │
                    │  web search tool) │
                    └──────────────────┘
```

(Diagram will be replaced with a proper illustration in `docs/architecture.md` once the server is running end-to-end.)

## Quickstart

```bash
git clone https://github.com/DoshiTirth/AnvilLLM.git
cd AnvilLLM
cp .env.example .env
docker compose up
```

Then open `http://localhost:8080` for the web UI, or hit the API directly:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-8b-instruct", "messages": [{"role": "user", "content": "Hello!"}]}'
```

*(Full instructions land with the `feat/llama-server-docker` and `feat/api-layer` PRs.)*

## Licensing & Attribution

AnvilLLM's own code (server, API, web UI, scripts) is licensed under the
[MIT License](LICENSE).

The **Llama 3.1 model weights** used by this project are separately licensed
under the [Llama 3.1 Community License](licenses/LICENSE-LLAMA3.1.txt) and
subject to Meta's [Acceptable Use Policy](licenses/LLAMA3.1-USE-POLICY.md).
This is a broad, mostly-free license (including commercial use) with a
few conditions — notably an additional commercial license requirement if
your product/service exceeds 700 million monthly active users. AnvilLLM
does not modify or redistribute the weights themselves; the download script
pulls them directly from the official source.

**Built with Llama.**

## Privacy

AnvilLLM has no telemetry and makes no calls to external LLM APIs. The only
outbound network calls are: (1) a one-time model weight download at setup,
(2) optional web search calls if you explicitly enable the RAG web-search
tool, and (3) standard package/container registry pulls during build.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Community-contributed configs and
examples live in [`examples/`](examples/) — please don't include any
proprietary or sensitive data in contributions.

## License

[MIT](LICENSE) for the AnvilLLM codebase. See above for model licensing.
