# Reliability & Observability

## Retries

Non-streaming requests to `llama-server` are retried automatically on
transient failures (connection errors, timeouts, upstream 502/503/504),
with exponential backoff (0.5s, 1s, 2s by default - 3 retries total). This
smooths over brief hiccups like a GC pause or momentary resource spike.

Streaming requests are **not** retried - once bytes have started flowing to
the client, retrying would mean either duplicating already-sent content or
silently truncating it. A connection failure before any bytes are sent
still raises cleanly and the client gets a clear error.

Non-retryable errors (e.g. a malformed request, 4xx) fail immediately
without wasting time on retries that can't succeed.

## Error responses

All errors use the same JSON shape as OpenAI's API:

```json
{"error": {"message": "...", "type": "..."}}
```

| Situation | Status | Type |
|---|---|---|
| llama-server unreachable after retries | 503 | `server_unavailable_error` |
| llama-server returned a 5xx after retries | 502 | `server_error` |
| llama-server returned a 4xx (bad request shape) | passthrough | `invalid_request_error` |
| Rate limit exceeded | 429 | `rate_limit_error` |
| Anything unexpected | 500 | `internal_error` |

Unhandled exceptions are always caught and turned into a clean 500 -
callers never see a raw stack trace. Full details go to the server logs
(see below) for debugging.

## Metrics

Prometheus-format metrics are exposed at `GET /metrics` (no auth required,
same as most metrics endpoints - put it behind your own network boundary
if it shouldn't be publicly reachable):

- `anvilllm_requests_total{method, path, status_code}` - request counts
- `anvilllm_request_duration_seconds{method, path}` - latency histogram
- `anvilllm_llama_server_errors_total{error_type}` - backend error counts

Like the request logs, metrics are numeric aggregates only - no prompt or
response content is ever recorded here.

Point a Prometheus instance at `/metrics` to scrape, or use `curl` to
sanity-check it directly:

```bash
curl http://localhost:8080/metrics
```
