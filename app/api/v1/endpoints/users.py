from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.schemas import User, UserCreate, UserUpdate, UserResponse
from app.core.exceptions import NotFoundException, ValidationException
from app.db.base import get_db
from app.db.service import UserService

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    search: Optional[str] = Query(None, description="Search users by name or email"),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination and search"""
    user_service = UserService(db)
    
    if search:
        users = await user_service.search_users(search, skip=skip, limit=limit)
    else:
        users = await user_service.get_users(skip=skip, limit=limit)
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific user by ID"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    return user


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    user_service = UserService(db)
    
    try:
        new_user = await user_service.create_user(
            email=user.email,
            full_name=user.full_name,
            password=user.password
        )
        return new_user
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update a user"""
    user_service = UserService(db)
    
    # Convert Pydantic model to dict, excluding unset fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Remove password from update data if present (should be handled separately)
    if "password" in update_data:
        del update_data["password"]
    
    try:
        updated_user = await user_service.update_user(user_id, **update_data)
        if not updated_user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return updated_user
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate a user (soft delete)"""
    user_service = UserService(db)
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    return {"message": f"User with ID {user_id} deactivated successfully"}
