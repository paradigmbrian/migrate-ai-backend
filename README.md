# MigrateAI Backend

A FastAPI-based backend for the MigrateAI application, providing immigration checklist generation and user management.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database with async support
- **Redis** - Caching and session storage
- **Alembic** - Database migration management
- **JWT Authentication** - Secure token-based authentication
- **Pydantic** - Data validation and serialization
- **Docker** - Containerized development environment

## Project Structure

```
migrate-backend/
├── app/
│   ├── api/           # API routes and endpoints
│   ├── core/          # Core configuration and utilities
│   ├── db/            # Database configuration and seeding
│   ├── models/        # SQLAlchemy ORM models
│   └── schemas/       # Pydantic data schemas
├── migrations/        # Alembic database migrations
├── scripts/           # Utility scripts
├── docker-compose.yml # Docker services configuration
├── Dockerfile         # Backend application container
└── pyproject.toml     # Project dependencies and configuration
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- uv (Python package manager)

### 1. Clone and Setup

```bash
# Navigate to backend directory
cd migrate-backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
```

### 2. Start Database Services

```bash
# Start PostgreSQL and Redis using Docker
./scripts/start-db.sh

# Or manually with Docker Compose
docker-compose up -d postgres redis
```

### 3. Run Database Migrations

```bash
# Apply database migrations
uv run alembic upgrade head

# Seed the database with initial data
uv run python -m app.db.seed
```

### 4. Start the Development Server

```bash
# Start the FastAPI server
uv run python -m app.main

# Or with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Docker Development

### Start All Services

```bash
# Start database services only
docker-compose up -d postgres redis

# Start everything (backend + databases)
docker-compose up -d
```

### Build and Run Backend Container

```bash
# Build the backend image
docker build -t migrate-backend .

# Run the container
docker run -p 8000:8000 --env-file .env migrate-backend
```

### Database Management

```bash
# View database logs
docker-compose logs -f postgres

# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d migrate_dev

# Reset database
docker-compose down -v
docker-compose up -d postgres redis
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# App Configuration
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/migrate_dev

# Redis
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8081"]
```

## Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Development

### Code Quality

```bash
# Format code
uv run black app/
uv run isort app/

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app
```

## API Endpoints

### Authentication (AWS Cognito)

- `POST /api/v1/auth/register` - User registration with Cognito
- `POST /api/v1/auth/login` - User login with Cognito
- `POST /api/v1/auth/logout` - User logout and token revocation
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/forgot-password` - Initiate password reset
- `POST /api/v1/auth/confirm-forgot-password` - Confirm password reset
- `POST /api/v1/auth/migrate-demo-users` - Migrate existing demo users to Cognito
- `POST /api/v1/auth/demo-login` - Demo login (legacy)

### Google OAuth (Production Only)

- `GET /api/v1/auth/google/auth-url` - Get Google OAuth authorization URL
- `POST /api/v1/auth/google/callback` - Handle Google OAuth callback
- `POST /api/v1/auth/google/login` - Login with Google ID token

### Users

- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user

### Countries

- `GET /api/v1/countries` - List all countries
- `GET /api/v1/countries/{country_id}` - Get country details
- `GET /api/v1/countries/{country_id}/policies` - Get country policies

### Checklists

- `GET /api/v1/checklists` - List user checklists
- `POST /api/v1/checklists` - Create new checklist
- `GET /api/v1/checklists/{checklist_id}` - Get checklist details
- `PUT /api/v1/checklists/{checklist_id}` - Update checklist
- `DELETE /api/v1/checklists/{checklist_id}` - Delete checklist

### Policies

- `GET /api/v1/policies` - List policies
- `POST /api/v1/policies` - Create policy
- `GET /api/v1/policies/{policy_id}` - Get policy details
- `PUT /api/v1/policies/{policy_id}` - Update policy
- `DELETE /api/v1/policies/{policy_id}` - Delete policy

## Database Models

### User

- Authentication fields (email, hashed_password)
- Profile information (name, phone, date_of_birth)
- Migration details (origin_country, destination_country, reason_for_moving)
- Timestamps and metadata

### Country

- Geographic information (name, code, continent, region)
- Economic data (gdp_per_capita, population)
- Immigration metrics (immigration_rate, visa_types)
- Policy information (policy_update_frequency)

### Checklist

- User association and status
- Origin and destination countries
- Progress tracking (completed_items, total_items)
- Timestamps and metadata

### ChecklistItem

- Checklist association and category
- Task details (title, description, priority)
- Completion tracking (is_completed, completed_at)
- Estimated duration and dependencies

### Policy

- Country association and policy type
- Requirements and eligibility criteria
- Processing times and costs
- Status and metadata

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.
