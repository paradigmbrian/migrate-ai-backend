#!/bin/bash

# Start database services using Docker Compose
echo "Starting MigrateAI database services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start the services
docker-compose up -d postgres redis

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 5

# Check if PostgreSQL is ready
echo "Checking PostgreSQL health..."
until docker-compose exec -T postgres pg_isready -U postgres -d migrate_dev; do
    echo "PostgreSQL is not ready yet. Waiting..."
    sleep 2
done

echo "✅ Database services started successfully!"
echo "PostgreSQL: localhost:5432"
echo "Redis: localhost:6379"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f" 