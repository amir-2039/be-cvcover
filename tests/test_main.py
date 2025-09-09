import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI Backend API"}


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_get_users():
    """Test getting all users"""
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 0


def test_get_user_by_id():
    """Test getting a specific user by ID"""
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert "email" in user
    assert "full_name" in user


def test_get_nonexistent_user():
    """Test getting a user that doesn't exist"""
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404


def test_create_user():
    """Test creating a new user"""
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "is_active": True,
        "password": "testpassword123"
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == user_data["email"]
    assert user["full_name"] == user_data["full_name"]


def test_auth_token():
    """Test authentication token endpoint"""
    form_data = {
        "username": "test@example.com",
        "password": "password"  # This matches the fake hashed password in auth.py
    }
    response = client.post("/api/v1/auth/token", data=form_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
