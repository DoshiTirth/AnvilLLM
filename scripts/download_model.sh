#!/usr/bin/env bash
# Downloads the default Llama 3.1 8B Instruct GGUF (Q4_K_M) from Hugging Face
# if it isn't already present, and verifies its checksum.
#
# Usage: ./scripts/download_model.sh [output_dir]
#
# NOTE: Downloading this model requires accepting Meta's Llama 3.1 license
# on Hugging Face (huggingface.co/meta-llama) with your own HF account first.
# Set HF_TOKEN in your .env if the repo you're pulling from requires auth.

set -euo pipefail

OUTPUT_DIR="${1:-./models}"
MODEL_FILE="llama-3.1-8b-instruct.Q4_K_M.gguf"
MODEL_PATH="${OUTPUT_DIR}/${MODEL_FILE}"

# Community GGUF re-packaging of meta-llama/Llama-3.1-8B-Instruct.
# Swap this URL if you prefer a different quantization or source.
MODEL_URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

# Expected SHA256 - fill in and pin this once you've verified your chosen
# source file, so future downloads are checked against a known-good hash.
EXPECTED_SHA256=""

mkdir -p "${OUTPUT_DIR}"

if [[ -f "${MODEL_PATH}" ]]; then
  echo "Model already present at ${MODEL_PATH}, skipping download."
else
  echo "Downloading model to ${MODEL_PATH} ..."
  AUTH_HEADER=()
  if [[ -n "${HF_TOKEN:-}" ]]; then
    AUTH_HEADER=(-H "Authorization: Bearer ${HF_TOKEN}")
  fi
  curl -L "${AUTH_HEADER[@]}" -o "${MODEL_PATH}" "${MODEL_URL}"
fi

if [[ -n "${EXPECTED_SHA256}" ]]; then
  echo "Verifying checksum..."
  ACTUAL_SHA256=$(sha256sum "${MODEL_PATH}" | awk '{print $1}')
  if [[ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]]; then
    echo "ERROR: checksum mismatch for ${MODEL_PATH}"
    echo "  expected: ${EXPECTED_SHA256}"
    echo "  actual:   ${ACTUAL_SHA256}"
    exit 1
  fi
  echo "Checksum OK."
else
  echo "WARNING: EXPECTED_SHA256 not set in this script - skipping verification."
  echo "Pin the hash after your first verified download for future integrity checks."
fi

echo "Done. Model ready at ${MODEL_PATH}"
