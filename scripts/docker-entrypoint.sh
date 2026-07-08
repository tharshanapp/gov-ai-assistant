#!/bin/bash
set -e

OLLAMA_HOST="${OLLAMA_BASE_URL:-http://ollama:11434}"
CHAT_MODEL="${OLLAMA_MODEL:-llama3.2}"
EMBED_MODEL="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

echo "==> Waiting for Ollama at ${OLLAMA_HOST}..."
for i in $(seq 1 60); do
  if curl -sf "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
    echo "==> Ollama is ready."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: Ollama did not start in time."
    exit 1
  fi
  sleep 3
done

pull_model() {
  local model="$1"
  if curl -sf "${OLLAMA_HOST}/api/tags" | grep -q "\"name\":\"${model}\""; then
    echo "==> Model already present: ${model}"
  else
    echo "==> Pulling model: ${model} (first deploy may take several minutes)..."
    curl -sf "${OLLAMA_HOST}/api/pull" -d "{\"name\":\"${model}\"}" || true
  fi
}

pull_model "${CHAT_MODEL}"
pull_model "${EMBED_MODEL}"

echo "==> Starting Government AI Assistant..."
exec streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true
