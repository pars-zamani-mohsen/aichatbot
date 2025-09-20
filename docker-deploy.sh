#!/bin/bash

# AI Chatbot Docker Deployment Script
# This script deploys the AI Chatbot application using Docker Compose

set -e

echo "🚀 Starting AI Chatbot Docker Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "env.docker" ]; then
    print_warning "env.docker file not found. Creating from template..."
    cp env.example env.docker
    print_warning "Please edit env.docker file with your configuration before running again."
    exit 1
fi

# Load environment variables
export $(cat env.docker | grep -v '^#' | xargs)

print_status "Environment variables loaded"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ssl
mkdir -p logs
mkdir -p data

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans

# Remove old images (optional)
if [ "$1" = "--clean" ]; then
    print_status "Cleaning up old images..."
    docker-compose down --rmi all --volumes --remove-orphans
fi

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check database
if docker-compose exec -T db pg_isready -U $POSTGRES_USER -d $POSTGRES_DB > /dev/null 2>&1; then
    print_success "Database is healthy"
else
    print_error "Database is not healthy"
    exit 1
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_error "Redis is not healthy"
    exit 1
fi

# Check Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API is healthy"
else
    print_error "Backend API is not healthy"
    exit 1
fi

# Check Frontend
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    print_success "Frontend is healthy"
else
    print_error "Frontend is not healthy"
    exit 1
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend alembic upgrade head

print_success "🎉 Deployment completed successfully!"
print_status "Services are running on:"
print_status "  - Frontend: http://localhost:3000"
print_status "  - Backend API: http://localhost:8000"
print_status "  - Nginx Proxy: http://localhost"
print_status "  - Database: localhost:5432"
print_status "  - Redis: localhost:6379"
print_status "  - ChromaDB: localhost:8001"
print_status "  - Ollama: localhost:11434"

print_status "To view logs: docker-compose logs -f"
print_status "To stop services: docker-compose down"
print_status "To restart services: docker-compose restart"
