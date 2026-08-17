# Contributing to AnvilLLM

Thanks for considering a contribution! A few guidelines to keep things smooth.

## Branching & PRs

- `main` is protected — all changes land via pull request.
- Use descriptive branch names: `feat/...`, `fix/...`, `docs/...`.
- Keep PRs focused and small where possible; easier to review, easier to revert.

## Before you open a PR

- Run linting/tests locally (`ruff check .`, `pytest`) once CI is in place.
- **Never commit secrets, API keys, tokens, internal URLs, or personal file paths.**
  Use `.env.example` for any new configuration variables — real values go in
  your own untracked `.env`.
- If contributing example configs or prompt templates, put them under
  `examples/` and keep them generic/reusable — no proprietary or
  company-specific data.

## Code style

- Python: follow `ruff` defaults (config will land with `feat/ci-cd`).
- Keep functions small and typed where practical (FastAPI + Pydantic already
  encourages this).

## Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`. Include repro steps,
expected vs actual behavior, and relevant logs (scrubbed of any secrets).

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
