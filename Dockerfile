# ==============================================================================
# Multi-Stage Production Dockerfile for Moza Vision Engine
# Base: Python 3.12-slim with non-root execution and minimal memory footprint
# ==============================================================================

# Stage 1: Dependency Builder
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
# Install wheel & build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies with headless OpenCV for containerized deployment
RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.30.0" \
    "websockets>=12.0" \
    "pydantic>=2.7.0" \
    "pydantic-settings>=2.2.0" \
    "loguru>=0.7.0" \
    "numpy>=1.24.0" \
    "opencv-python-headless>=4.8.0" \
    "onnxruntime>=1.17.0" \
    "simpleeval>=0.9.13" \
    "scipy>=1.11.0"


# Stage 2: Production Minimal Runtime
FROM python:3.12-slim AS runner

LABEL org.opencontainers.image.title="moza-vision" \
      org.opencontainers.image.description="Autonomous edge vision, cocktail perception & venue spatial intelligence engine" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install runtime dependencies (ffmpeg for video encoding and curl for health probes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src" \
    MOZA_MODEL_DIR="/app/models"

# Create unprivileged system user
RUN groupadd -r moza && useradd -r -g moza -d /app -s /sbin/nologin moza && \
    mkdir -p /app/data /app/configs /app/models && \
    curl -fsSL -o /app/models/yolox_s.onnx \
      https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_s.onnx && \
    chown -R moza:moza /app

# Copy application source code and configurations
COPY --chown=moza:moza src/ /app/src/
COPY --chown=moza:moza services/ /app/services/
COPY --chown=moza:moza configs/ /app/configs/

USER moza

EXPOSE 8100

# Periodic container health probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# Launch Moza Server daemon
CMD ["uvicorn", "services.moza_server.main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "1"]
