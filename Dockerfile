# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim AS runtime

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    TZ=UTC

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/instance /app/data

# Copy wheels from builder stage and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy only necessary files
COPY app.py docker-entrypoint.sh init_db.py ./
COPY akowe/ ./akowe/

# Copy migrations and make sure directories exist
COPY migrations/ ./migrations/
RUN mkdir -p /app/migrations/versions

# Copy Python package files if they exist
COPY pyproject.toml setup.cfg setup.py alembic.ini ./

# Create data directory
RUN mkdir -p /app/data

# Create empty placeholder files if needed
RUN touch /app/data/.keep

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user for security
RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    chown -R app:app /app

# Use non-root user
USER app

# Create volume mount points for persistent data
VOLUME ["/app/instance", "/app/data"]

# Expose application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (configuration is handled in the entrypoint script)
CMD ["gunicorn"]