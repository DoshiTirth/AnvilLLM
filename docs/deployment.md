# Deployment

## Quickstart (CPU)

```bash
cp .env.example .env
./scripts/download_model.sh
docker compose up llama-server
```

This builds `llama.cpp`'s server from source (CPU-only by default) and starts
it on `localhost:8081` with the Llama 3.1 8B Q4_K_M model.

Test it directly (llama.cpp's own OpenAI-compatible endpoint, before the
AnvilLLM API layer is in front of it):

```bash
curl http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## Hardware notes

- **CPU only:** works fine for 8B at Q4_K_M, expect a few tokens/sec depending
  on core count. Good for development and light usage.
- **Modest single GPU:** llama.cpp supports partial GPU offload
  (`--n-gpu-layers`) to speed up generation even without enough VRAM to hold
  the whole model. Add this flag to the `command:` block in
  `docker-compose.yml` once you know your VRAM budget.
- **Serious dedicated GPU / high throughput:** consider vLLM instead of
  llama.cpp — outside this project's current scope, but the API layer's
  OpenAI-compatible shape means swapping the backend later wouldn't require
  changing client code.

## Choosing a different quantization or model

Edit `MODEL_URL` in `scripts/download_model.sh`, or set `MODEL_FILENAME` in
your `.env` if you've already got a GGUF file in `./models/`. Lower quant
levels (e.g. Q3) use less RAM/VRAM at some quality cost; higher levels
(Q5/Q6/Q8) use more but stay closer to full precision.

## Production notes

- Remove the `8081:8081` port mapping in `docker-compose.yml` once the `api`
  service (added in `feat/api-layer`) is in place — llama-server should only
  be reachable internally, not exposed directly.
- Pin `EXPECTED_SHA256` in `scripts/download_model.sh` after your first
  verified download, so future deploys fail loudly on a corrupted/tampered
  download instead of silently running an unverified binary blob.
