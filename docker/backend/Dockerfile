FROM python:3.11-slim

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

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt requirements.txt

# Install Python dependencies with increased timeout
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

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

# Expose port
EXPOSE 8000

# Copy supervisor configuration
COPY docker/backend/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
