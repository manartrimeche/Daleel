# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Dockerfile
# Multi-stage build: frontend (Node) → backend (Python) → runtime
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1 : Frontend (React/Vite) ──────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2 : Backend Python (dependencies) ──────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies (for sentence-transformers, faiss-cpu, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for smaller final image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 3 : Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# System deps: Tesseract OCR + poppler (for PyMuPDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"

# Copy application code
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist/ ./interface-daleel/

# Create non-root user and uploads directory
RUN groupadd --gid 1001 daleel && \
    useradd --uid 1001 --gid daleel --shell /bin/false daleel && \
    mkdir -p uploads && chown daleel:daleel uploads

# Expose FastAPI port (défaut local ; surchargé par $PORT en hébergement)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT','8000')}/api/v1/health\")" || exit 1

# Switch to non-root user
USER daleel

# Run the application — le port est configurable ($PORT) pour Hugging Face
# Spaces / Railway / Render ; il vaut 8000 par défaut (dev local, docker-compose).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
