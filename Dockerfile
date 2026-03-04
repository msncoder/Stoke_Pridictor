# ──────────────────────────────────────────────────────────────────────────────
# Hugging Face Spaces – FastAPI Backend
# ──────────────────────────────────────────────────────────────────────────────
# HF Spaces requirements:
#   • Expose port 7860  (HF routes external traffic here)
#   • Run as non-root user UID=1000  (HF enforces this)
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.10-slim

# ── System dependencies ───────────────────────────────────────────────────────
# libpq-dev      → psycopg2-binary (Neon DB)
# libcurl4-openssl-dev + libssl-dev → curl_cffi
# gcc / g++ / python3-dev → compile any native wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gcc \
        g++ \
        python3-dev \
        libpq-dev \
        libcurl4-openssl-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user required by Hugging Face Spaces ────────────────────────────
RUN useradd -m -u 1000 appuser

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# Give the non-root user ownership of the app directory
RUN chown -R appuser:appuser /app

# ── Environment ───────────────────────────────────────────────────────────────
# HF Spaces always uses port 7860 — do NOT change this
ENV PORT=7860

# Suppress TensorFlow C++ INFO/WARNING spam in logs
ENV TF_CPP_MIN_LOG_LEVEL=2

# Prevents Python from buffering stdout/stderr (shows logs in real-time)
ENV PYTHONUNBUFFERED=1

# ── Switch to non-root user ───────────────────────────────────────────────────
USER 1000

# ── Start the API ─────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
