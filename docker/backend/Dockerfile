# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    supervisor \
    nginx \
    libmagic1t64 \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies installation with cache
FROM base as dependencies

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt requirements.txt

# Install PyTorch CPU version first (smaller download)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --timeout 3600 torch==2.2.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other Python dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --timeout 3600 -r requirements.txt

# Stage 3: Final application image
FROM base as final

# Set work directory
WORKDIR /app

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /var/log/supervisor \
    && mkdir -p /app/logs \
    && mkdir -p /app/processed_data \
    && mkdir -p /app/uploads \
    && mkdir -p /app/knowledge_base \
    && mkdir -p /app/chroma_db \
    && mkdir -p /app/temp

# Set permissions
RUN chmod +x /app/run.py
RUN chmod +x /app/create_admin_user.py
RUN chmod +x /app/docker_init.py
RUN chmod +x /app/seed_system_settings.py

# Expose port
EXPOSE 8000

# Copy supervisor configuration
COPY docker/backend/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]