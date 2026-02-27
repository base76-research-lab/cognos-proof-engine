# Multi-stage build for smaller image
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and pre-install wheels
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Final image
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 cognos && \
    mkdir -p /data && \
    chown -R cognos:cognos /data

# Copy Python packages from builder
COPY --from=builder /root/.local /home/cognos/.local

# Copy application
COPY src/ src/
COPY .env.example .env

# Set environment
ENV PATH=/home/cognos/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    COGNOS_MOCK_UPSTREAM=true \
    COGNOS_TRACE_DB=/data/traces.sqlite3

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8788/healthz')" || exit 1

# Switch to non-root user
USER cognos

# Expose port
EXPOSE 8788

# Run
CMD ["python3", "-m", "uvicorn", "--app-dir", "src", "main:app", "--host", "0.0.0.0", "--port", "8788"]
