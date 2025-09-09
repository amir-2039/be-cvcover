# FastAPI Backend Application

A modern, fast, and scalable Python API backend built with FastAPI.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🔐 **Authentication** - JWT-based authentication system
- 📊 **Pydantic Models** - Data validation and serialization
- 🗄️ **Database Ready** - SQLAlchemy integration (PostgreSQL)
- 🔄 **Redis Support** - Caching and session management
- 📝 **Auto Documentation** - Interactive API docs with Swagger UI
- 🧪 **Testing** - Pytest integration
- 🐳 **Docker Ready** - Containerization support

## Project Structure

```
be-cvcover/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # API router configuration
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py     # Authentication endpoints
│   │           └── users.py    # User management endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application configuration
│   │   └── exceptions.py       # Custom exception handlers
│   └── models/
│       ├── __init__.py
│       └── schemas.py          # Pydantic models
├── requirements.txt            # Python dependencies
├── env.example                # Environment variables template
└── README.md                  # This file
```

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to the project directory
cd be-cvcover

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy the environment template
cp env.example .env

# Edit .env file with your configuration
# At minimum, update the SECRET_KEY for production
```

### 3. Run the Application

```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python app/main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Login and get access token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/register` - Register new user

### Users
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get specific user
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Health Check
- `GET /` - Welcome message
- `GET /health` - Health check endpoint

## Development

### Adding New Endpoints

1. Create a new router in `app/api/v1/endpoints/`
2. Add the router to `app/api/v1/api.py`
3. Define Pydantic models in `app/models/schemas.py`

### Database Integration

The project is set up for PostgreSQL with SQLAlchemy. To add database functionality:

1. Update `DATABASE_URL` in your `.env` file
2. Create database models in `app/models/`
3. Add database session management in `app/core/`

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## Production Deployment

### Environment Variables

Make sure to set these in production:

- `SECRET_KEY` - Strong secret key for JWT tokens
- `DATABASE_URL` - Production database connection
- `ENVIRONMENT=production`
- `DEBUG=false`

### Docker Deployment

```bash
# Build Docker image
docker build -t fastapi-backend .

# Run container
docker run -p 8000:8000 fastapi-backend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
