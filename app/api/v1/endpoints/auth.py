from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.schemas import Token, UserResponse
from app.core.exceptions import UnauthorizedException

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock user for authentication demo
fake_users_db = {
    "test@example.com": {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "hashed_password": "fakehashedpassword"  # In real app, use proper password hashing
    }
}


def fake_hash_password(password: str):
    return "fakehashed" + password


def get_user(email: str):
    if email in fake_users_db:
        user_dict = fake_users_db[email]
        return user_dict


def fake_verify_password(plain_password, hashed_password):
    return fake_hash_password(plain_password) == hashed_password


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token"""
    user = get_user(form_data.username)
    if not user:
        raise UnauthorizedException("Incorrect email or password")
    if not fake_verify_password(form_data.password, user["hashed_password"]):
        raise UnauthorizedException("Incorrect email or password")
    
    # In a real application, you would generate a proper JWT token here
    access_token = "fake-access-token"
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    """Get current user information"""
    # In a real application, you would verify the JWT token here
    if token != "fake-access-token":
        raise UnauthorizedException("Invalid token")
    
    user = get_user("test@example.com")
    return user


@router.post("/register")
async def register(email: str, password: str, full_name: str):
    """Register a new user"""
    if email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    fake_users_db[email] = {
        "id": len(fake_users_db) + 1,
        "email": email,
        "full_name": full_name,
        "is_active": True,
        "hashed_password": fake_hash_password(password)
    }
    
    return {"message": "User registered successfully"}
