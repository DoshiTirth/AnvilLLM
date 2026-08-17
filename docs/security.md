# Security

## API keys

By default (`API_KEYS` unset), AnvilLLM's API has **no authentication** —
fine for local development, not fine for anything reachable beyond your own
machine.

Generate a key:

```bash
./scripts/generate_api_key.sh
```

Set one or more (comma-separated) in `.env`:

```
API_KEYS=anvil-xxxxxxxxxxxx,anvil-yyyyyyyyyyyy
```

Multiple keys let you issue a separate one per client/service and revoke
individually by removing it from the list, without rotating everyone else's.

Requests must then include:

```
Authorization: Bearer anvil-xxxxxxxxxxxx
```

Key comparison uses `hmac.compare_digest` (constant-time), so response
timing can't be used to guess a valid key character-by-character.

## Rate limiting

Enforced per API key (or per source IP when auth is disabled), via
`RATE_LIMIT_PER_MINUTE` in `.env` (default: 60 requests/minute). Exceeding
it returns HTTP 429 with a JSON error body.

This uses an in-memory limiter — correct for a single AnvilLLM instance.
If you ever run multiple replicas behind a load balancer, in-memory limits
won't be shared across them; you'd need a shared backend (e.g. Redis)
instead.

`/v1/rag/ingest` has an additional, stricter limit (20/minute) since
document ingestion is more expensive than a typical request.

## Secrets management

- Never commit `.env` — it's gitignored. Only `.env.example` (placeholders)
  is tracked.
- Rotate API keys periodically, and immediately if one may have been
  exposed (pasted into a chat, committed by mistake, etc.).
- If deploying via Docker Compose on a shared host, prefer passing secrets
  through your orchestrator's secret store (Docker secrets, Kubernetes
  secrets, etc.) over plain `.env` files where possible.
- The web search API key (`WEB_SEARCH_API_KEY`, if RAG web search is
  enabled) follows the same rules — treat it as sensitive.

## Logging

Every request is logged as a single JSON line to stdout: timestamp, request
ID, method, path, status code, duration, and a **hashed** caller identity
(SHA-256, truncated) - never the raw API key or IP address, and never
request/response bodies. This means prompts, completions, and ingested
document text never end up in log files, even at DEBUG level.

Configure via `.env`:

```
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
LOG_JSON=true         # false for human-readable single-line logs (local dev)
```

Each response also includes an `X-Request-ID` header matching its log line,
useful for correlating a specific request a user reports with your logs.

## Reporting a vulnerability

Open an issue using the bug report template, or contact the maintainers
directly for anything sensitive enough that it shouldn't be public before
a fix ships.
