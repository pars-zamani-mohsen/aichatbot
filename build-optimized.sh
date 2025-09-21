#!/bin/bash

# Optimized Docker Build Script with BuildKit and Cache
# This script enables BuildKit and uses cache mounts for faster builds

echo "🚀 Starting optimized Docker build..."

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with cache mount and inline cache
echo "📦 Building backend with BuildKit cache..."
docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1 backend

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Backend build completed successfully!"
    echo "🔄 Starting services..."
    docker-compose up -d
else
    echo "❌ Build failed!"
    exit 1
fi

echo "🎉 All services are running!"
echo "📊 Build time optimized with:"
echo "   - Multi-stage build"
echo "   - BuildKit cache mounts"
echo "   - Layer caching"
echo "   - Inline cache"
