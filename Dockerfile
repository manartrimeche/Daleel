# ─────────────────────────────────────────────────────────────────────────────
# Daleel — Dockerfile
# Multi-stage build for a production-ready FastAPI application.
# ─────────────────────────────────────────────────────────────────────────────

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

# ── Runtime stage ──
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

# Copy application code
COPY app/ ./app/
COPY training/ ./training/
COPY README.md RAPPORT_PROJET.md COMPLIANCE_STEERING.md ./

# Create uploads directory
RUN mkdir -p uploads

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
