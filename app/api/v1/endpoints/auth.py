from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import Token, UserResponse, UserCreate
from app.core.exceptions import UnauthorizedException, ValidationException
from app.db.base import get_db
from app.db.service import AuthService, UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    auth_service = AuthService(db)
    
    # Get client IP and user agent
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    session = await auth_service.login(
        email=form_data.username,
        password=form_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not session:
        raise UnauthorizedException("Incorrect email or password")
    
    return {"access_token": session.session_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    auth_service = AuthService(db)
    
    user = await auth_service.get_current_user(token)
    if not user:
        raise UnauthorizedException("Invalid token")
    
    return user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    user_service = UserService(db)
    
    try:
        user = await user_service.create_user(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password
        )
        return user
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Logout user by invalidating session"""
    auth_service = AuthService(db)
    
    success = await auth_service.logout(token)
    if not success:
        raise UnauthorizedException("Invalid token")
    
    return {"message": "Successfully logged out"}


@router.post("/refresh")
async def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Refresh user session"""
    auth_service = AuthService(db)
    
    session = await auth_service.refresh_session(token)
    if not session:
        raise UnauthorizedException("Invalid token")
    
    return {"access_token": session.session_token, "token_type": "bearer"}
