#!/bin/bash

# Production startup script for MigrateAI Backend
# This mimics AWS ECS deployment patterns

set -e

echo "🚀 Starting MigrateAI Backend in Production Mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if production environment file exists
if [ ! -f .env.prod ]; then
    echo "⚠️  Warning: .env.prod not found. Creating from template..."
    cp .env.prod.example .env.prod 2>/dev/null || echo "Please create .env.prod with your production values"
fi

# Load production environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
    echo "✅ Production environment loaded"
else
    echo "⚠️  Using default environment variables"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

# Build and start production services
echo "🔨 Building production images..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Test database connection
echo "🗄️  Testing database connection..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U migrate_user -d migrate_prod

# Run database migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend /app/.venv/bin/alembic upgrade head

# Seed database if needed
echo "🌱 Seeding database..."
docker-compose -f docker-compose.prod.yml exec -T backend /app/.venv/bin/python -m app.db.seed

# Test API health
echo "🏥 Testing API health..."
sleep 5
curl -f http://localhost:8000/health

echo ""
echo "✅ Production environment is ready!"
echo "📊 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  Restart backend: docker-compose -f docker-compose.prod.yml restart backend" 