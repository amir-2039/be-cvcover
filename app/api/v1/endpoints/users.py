from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import User, UserCreate, UserUpdate, UserResponse
from app.core.exceptions import NotFoundException

router = APIRouter()

# Mock data for demonstration
users_db = [
    {
        "id": 1,
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "is_active": True,
        "created_at": "2024-01-02T00:00:00",
        "updated_at": "2024-01-02T00:00:00"
    }
]


@router.get("/", response_model=List[UserResponse])
async def get_users():
    """Get all users"""
    return users_db


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a specific user by ID"""
    user = next((user for user in users_db if user["id"] == user_id), None)
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
    return user


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    new_user = {
        "id": len(users_db) + 1,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    users_db.append(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate):
    """Update a user"""
    user_index = next((i for i, user in enumerate(users_db) if user["id"] == user_id), None)
    if user_index is None:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    user = users_db[user_index]
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user["updated_at"] = "2024-01-01T00:00:00"  # In real app, use datetime.now()
    users_db[user_index] = user
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    user_index = next((i for i, user in enumerate(users_db) if user["id"] == user_id), None)
    if user_index is None:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    users_db.pop(user_index)
    return {"message": f"User with ID {user_id} deleted successfully"}
