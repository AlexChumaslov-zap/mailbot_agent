# --- Stage 1: Install dependencies ---
# Using a slim base keeps the image small (~150MB base vs ~900MB for full)
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies first, separately from app code.
# Docker caches each step — so if your code changes but requirements.txt
# doesn't, Docker reuses the cached dependencies instead of reinstalling.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final image ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/
COPY main.py .
COPY entrypoint.sh .

# docs/ and faiss_index/ are mounted at runtime or downloaded from S3
# so they are NOT baked into the image

EXPOSE 8000

ENTRYPOINT ["bash", "entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
