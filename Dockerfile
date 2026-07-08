FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY .streamlit/config.toml .streamlit/config.toml
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

RUN mkdir -p data_source .index_cache

ENV AI_PROVIDER=ollama \
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=llama3.2 \
    OLLAMA_EMBED_MODEL=nomic-embed-text \
    ADMIN_PASSWORD=admin123

EXPOSE 8501

ENTRYPOINT ["/docker-entrypoint.sh"]
