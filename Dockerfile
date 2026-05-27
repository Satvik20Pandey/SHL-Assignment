FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch keeps image RAM usage within Render free tier limits.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu --force-reinstall

COPY . .
RUN python scripts/build_catalog.py \
    && python scripts/build_index_cache.py

ENV PYTHONUNBUFFERED=1
ENV CATALOG_PATH=/app/data/catalog.json
ENV INDEX_CACHE_DIR=/app/data/index_cache
ENV HF_HOME=/app/data/hf_cache
ENV TRANSFORMERS_CACHE=/app/data/hf_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/data/hf_cache
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
