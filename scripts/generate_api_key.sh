#!/usr/bin/env bash
# Generates a cryptographically random API key suitable for API_KEYS in .env.
#
# Usage: ./scripts/generate_api_key.sh

set -euo pipefail

python3 -c "import secrets; print('anvil-' + secrets.token_urlsafe(32))"
