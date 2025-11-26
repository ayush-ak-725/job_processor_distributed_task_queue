"""Authentication middleware"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.infrastructure.persistence.database import get_db
from app.core.domain.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    api_key = credentials.credentials
    
    # Hash the API key (in production, you'd hash it the same way when creating users)
    # For simplicity, we'll do a direct comparison, but in production use hashing
    user_repo = UserRepository(db)
    
    # Try to find user by API key hash
    # Note: In production, hash the incoming API key and compare
    # For prototype, we'll do a simple lookup
    user = await user_repo.get_by_api_key_hash(api_key)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return user

