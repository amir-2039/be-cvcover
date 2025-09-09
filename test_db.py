#!/usr/bin/env python3
"""
Database connection test script
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))

from app.db.base import engine, init_db
from app.db.service import UserService
from app.db.base import AsyncSessionLocal


async def test_database():
    """Test database connection and basic operations"""
    print("🔍 Testing database connection...")
    
    try:
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ Database connection successful")
        
        # Initialize database tables
        await init_db()
        print("✅ Database tables created/verified")
        
        # Test user creation
        async with AsyncSessionLocal() as session:
            user_service = UserService(session)
            
            # Create a test user
            test_user = await user_service.create_user(
                email="test@example.com",
                full_name="Test User",
                password="testpassword123"
            )
            print(f"✅ Test user created: {test_user.email}")
            
            # Test user retrieval
            retrieved_user = await user_service.get_user(test_user.id)
            print(f"✅ User retrieved: {retrieved_user.full_name}")
            
            # Test authentication
            auth_user = await user_service.authenticate_user(
                "test@example.com", 
                "testpassword123"
            )
            print(f"✅ User authentication successful: {auth_user.email}")
        
        print("\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)
