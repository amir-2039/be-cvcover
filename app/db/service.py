"""
Database service layer for business logic
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import bcrypt
import secrets

from app.db.repositories import (
    UserRepository, 
    UserSessionRepository, 
    AuditLogRepository,
    SystemConfigRepository
)
from app.db.models import User, UserSession
from app.core.exceptions import NotFoundException, UnauthorizedException, ValidationException


class UserService:
    """User service for business logic"""
    
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.session_repo = UserSessionRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def create_user(self, email: str, full_name: str, password: str) -> User:
        """Create a new user with hashed password"""
        hashed_password = self._hash_password(password)
        
        user = await self.user_repo.create_user(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password
        )
        
        # Log the action
        await self.audit_repo.log_action(
            user_id=user.id,
            action="user_created",
            resource_type="user",
            resource_id=str(user.id),
            details=f"User {email} created"
        )
        
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            return None
        
        if not self._verify_password(password, user.hashed_password):
            return None
        
        return user

    async def create_user_session(self, user: User, ip_address: str = None, 
                                user_agent: str = None) -> UserSession:
        """Create a new user session"""
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour session
        
        session = await self.session_repo.create_session(
            user_id=user.id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log the action
        await self.audit_repo.log_action(
            user_id=user.id,
            action="user_login",
            resource_type="session",
            resource_id=str(session.id),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session

    async def get_user_by_session(self, session_token: str) -> Optional[User]:
        """Get user by session token"""
        session = await self.session_repo.get_by_token(session_token)
        if not session:
            return None
        
        return await self.user_repo.get_by_id(User, session.user_id)

    async def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session"""
        session = await self.session_repo.get_by_token(session_token)
        if not session:
            return False
        
        # Log the action
        await self.audit_repo.log_action(
            user_id=session.user_id,
            action="user_logout",
            resource_type="session",
            resource_id=str(session.id)
        )
        
        return await self.session_repo.invalidate_session(session_token)

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repo.get_by_id(User, user_id)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return await self.user_repo.get_active_users(skip=skip, limit=limit)

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user"""
        user = await self.user_repo.update_user(user_id, **kwargs)
        
        if user:
            # Log the action
            await self.audit_repo.log_action(
                user_id=user_id,
                action="user_updated",
                resource_type="user",
                resource_id=str(user_id),
                details=f"Updated fields: {', '.join(kwargs.keys())}"
            )
        
        return user

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user"""
        user = await self.user_repo.deactivate_user(user_id)
        
        if user:
            # Log the action
            await self.audit_repo.log_action(
                user_id=user_id,
                action="user_deactivated",
                resource_type="user",
                resource_id=str(user_id)
            )
            return True
        
        return False

    async def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users"""
        return await self.user_repo.search_users(query, skip=skip, limit=limit)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class AuthService:
    """Authentication service"""
    
    def __init__(self, session: AsyncSession):
        self.user_service = UserService(session)
        self.audit_repo = AuditLogRepository(session)

    async def login(self, email: str, password: str, ip_address: str = None, 
                   user_agent: str = None) -> Optional[UserSession]:
        """Login user and create session"""
        user = await self.user_service.authenticate_user(email, password)
        if not user:
            # Log failed login attempt
            await self.audit_repo.log_action(
                action="login_failed",
                details=f"Failed login attempt for email: {email}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return None
        
        return await self.user_service.create_user_session(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )

    async def logout(self, session_token: str) -> bool:
        """Logout user"""
        return await self.user_service.logout_user(session_token)

    async def get_current_user(self, session_token: str) -> Optional[User]:
        """Get current user from session token"""
        return await self.user_service.get_user_by_session(session_token)

    async def refresh_session(self, session_token: str) -> Optional[UserSession]:
        """Refresh session (extend expiry)"""
        session = await self.user_service.session_repo.get_by_token(session_token)
        if not session:
            return None
        
        # Extend session by 24 hours
        session.expires_at = datetime.utcnow() + timedelta(hours=24)
        return await self.user_service.session_repo.update(session)


class SystemService:
    """System service for configuration and maintenance"""
    
    def __init__(self, session: AsyncSession):
        self.config_repo = SystemConfigRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def get_config(self, key: str) -> Optional[str]:
        """Get system configuration"""
        return await self.config_repo.get_config(key)

    async def set_config(self, key: str, value: str, description: str = None) -> bool:
        """Set system configuration"""
        config = await self.config_repo.set_config(key, value, description)
        
        # Log the action
        await self.audit_repo.log_action(
            action="config_updated",
            resource_type="config",
            resource_id=key,
            details=f"Config {key} updated"
        )
        
        return config is not None

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        count = await self.user_service.session_repo.cleanup_expired_sessions()
        
        # Log the action
        await self.audit_repo.log_action(
            action="cleanup_sessions",
            details=f"Cleaned up {count} expired sessions"
        )
        
        return count
