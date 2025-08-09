# MigrateAI Backend API

A FastAPI-based backend for the MigrateAI application, providing immigration checklist management, user authentication, and AI-powered personalization features.

## Features

- **AWS Cognito Authentication**: Secure user authentication with social login support
- **AI-Powered Checklists**: OpenAI integration for personalized checklist generation
- **Policy Change Detection**: Automated monitoring of immigration policy changes
- **User Management**: Profile management and user preferences
- **Country Data**: Comprehensive country information and visa requirements
- **Real-time Updates**: WebSocket support for real-time data synchronization

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (for caching and sessions)
- OpenAI API key (for AI features)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd migrate-backend
   ```

2. **Install dependencies**

   ```bash
   pip install -e .
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/migrate_ai

# AWS Cognito
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret
COGNITO_REGION=us-east-1

# Google OAuth (Production Only)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
BACKEND_URL=http://localhost:8000

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379
```

## API Documentation

Once the server is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## API Endpoints

### Authentication (AWS Cognito)

- `POST /api/v1/auth/register` - User registration with Cognito
- `POST /api/v1/auth/login` - User login with Cognito
- `POST /api/v1/auth/logout` - User logout and token revocation
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/forgot-password` - Initiate password reset
- `POST /api/v1/auth/confirm-forgot-password` - Confirm password reset

### Google OAuth (Production Only)

- `GET /api/v1/auth/google/auth-url` - Get Google OAuth authorization URL
- `POST /api/v1/auth/google/callback` - Handle Google OAuth callback
- `POST /api/v1/auth/google/login` - Login with Google ID token

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `DELETE /api/v1/users/me` - Delete current user account

### Profile Management

- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/profile/onboarding` - Complete onboarding

### Checklists

- `GET /api/v1/checklists` - Get user checklists
- `POST /api/v1/checklists` - Create new checklist
- `GET /api/v1/checklists/{checklist_id}` - Get specific checklist
- `PUT /api/v1/checklists/{checklist_id}` - Update checklist
- `DELETE /api/v1/checklists/{checklist_id}` - Delete checklist

### AI-Powered Checklists

- `POST /api/v1/ai-checklists/generate` - Generate AI-powered personalized checklist
- `GET /api/v1/ai-checklists/recommendations` - Get personalized recommendations
- `POST /api/v1/ai-checklists/tips` - Get smart tips for specific tasks
- `GET /api/v1/ai-checklists/health` - Check AI service health

### Personalization Features

- `GET /api/v1/ai-checklists/user-profile` - Get user's personalization profile
- `GET /api/v1/ai-checklists/dynamic-content/{origin_id}/{destination_id}` - Get dynamic content for country pair
- `GET /api/v1/ai-checklists/smart-defaults/{origin_id}/{destination_id}` - Get smart defaults and suggestions
- `POST /api/v1/ai-checklists/personalized-tips` - Get personalized tips and advice

### Policy Change Detection

- `POST /api/v1/policy-monitoring/check-changes` - Manually trigger policy change check
- `GET /api/v1/policy-monitoring/user-changes` - Get policy changes relevant to user
- `POST /api/v1/policy-monitoring/assess-impact` - Assess impact of policy change on checklists
- `GET /api/v1/policy-monitoring/notification-preferences` - Get user notification preferences
- `PUT /api/v1/policy-monitoring/notification-preferences` - Update notification preferences
- `GET /api/v1/policy-monitoring/monitoring-status` - Get monitoring system status

### Countries

- `GET /api/v1/countries` - Get all countries
- `GET /api/v1/countries/{country_id}` - Get specific country
- `GET /api/v1/countries/search` - Search countries

### Policies

- `GET /api/v1/policies` - Get immigration policies
- `GET /api/v1/policies/{policy_id}` - Get specific policy
- `GET /api/v1/policies/country/{country_id}` - Get policies for country

### Data Collection

- `POST /api/v1/data-collection/feedback` - Submit user feedback
- `GET /api/v1/data-collection/analytics` - Get analytics data

## Testing

### Run Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov=app tests/
```

## Development

### Code Style

This project uses:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

### Pre-commit Hooks

```bash
pre-commit install
```

## Deployment

### Docker

```bash
docker build -t migrate-ai-backend .
docker run -p 8000:8000 migrate-ai-backend
```

### AWS ECS

See `infrastructure/aws/`
