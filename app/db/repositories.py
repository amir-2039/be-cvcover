"""
Repository pattern for database operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import hashlib
import secrets

from app.db.models import User, UserSession, AuditLog, APIKey, SystemConfig
from app.core.exceptions import NotFoundException, ValidationException


class BaseRepository:
    """Base repository class with common operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, model_instance):
        """Create a new record"""
        self.session.add(model_instance)
        await self.session.commit()
        await self.session.refresh(model_instance)
        return model_instance

    async def get_by_id(self, model_class, record_id: int):
        """Get record by ID"""
        result = await self.session.execute(
            select(model_class).where(model_class.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, model_class, skip: int = 0, limit: int = 100):
        """Get all records with pagination"""
        result = await self.session.execute(
            select(model_class).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(self, model_instance):
        """Update a record"""
        await self.session.commit()
        await self.session.refresh(model_instance)
        return model_instance

    async def delete(self, model_instance):
        """Delete a record"""
        await self.session.delete(model_instance)
        await self.session.commit()


class UserRepository(BaseRepository):
    """User repository with user-specific operations"""
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_user(self, email: str, full_name: str, hashed_password: str) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_by_email(email)
        if existing_user:
            raise ValidationException("User with this email already exists")
        
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True
        )
        return await self.create(user)

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields"""
        user = await self.get_by_id(User, user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        return await self.update(user)

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user"""
        return await self.update_user(user_id, is_active=False)

    async def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email"""
        search_filter = or_(
            User.full_name.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
        
        result = await self.session.execute(
            select(User)
            .where(search_filter)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class UserSessionRepository(BaseRepository):
    """User session repository"""
    
    async def create_session(self, user_id: int, expires_at: datetime, 
                           ip_address: str = None, user_agent: str = None) -> UserSession:
        """Create a new user session"""
        session_token = self._generate_session_token()
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return await self.create(session)

    async def get_by_token(self, token: str) -> Optional[UserSession]:
        """Get session by token"""
        result = await self.session.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.session_token == token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()

    async def invalidate_session(self, token: str) -> bool:
        """Invalidate a session"""
        session = await self.get_by_token(token)
        if session:
            session.is_active = False
            await self.update(session)
            return True
        return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        result = await self.session.execute(
            update(UserSession)
            .where(UserSession.expires_at < datetime.utcnow())
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount

    def _generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)


class AuditLogRepository(BaseRepository):
    """Audit log repository"""
    
    async def log_action(self, user_id: int = None, action: str = None, 
                        resource_type: str = None, resource_id: str = None,
                        details: str = None, ip_address: str = None, 
                        user_agent: str = None) -> AuditLog:
        """Log an action"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return await self.create(audit_log)

    async def get_user_actions(self, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get actions for a specific user"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_actions(self, hours: int = 24, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get recent actions"""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.created_at >= since)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class SystemConfigRepository(BaseRepository):
    """System configuration repository"""
    
    async def get_config(self, key: str) -> Optional[str]:
        """Get configuration value by key"""
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        return config.value if config else None

    async def set_config(self, key: str, value: str, description: str = None) -> SystemConfig:
        """Set configuration value"""
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value
            if description:
                config.description = description
            return await self.update(config)
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description
            )
            return await self.create(config)

    async def get_all_configs(self) -> Dict[str, str]:
        """Get all configuration values"""
        result = await self.session.execute(select(SystemConfig))
        configs = result.scalars().all()
        return {config.key: config.value for config in configs}
