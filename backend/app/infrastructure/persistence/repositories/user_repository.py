"""User repository implementation"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User
from app.infrastructure.persistence.models.job_model import UserModel


class UserRepository:
    """Repository for user data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[User]:
        """Get user by API key hash"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.api_key_hash == api_key_hash)
        )
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None
        return self._model_to_domain(user_model)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None
        return self._model_to_domain(user_model)
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        user_model = UserModel(
            id=user.id,
            api_key_hash=user.api_key_hash,
            name=user.name,
            max_concurrent_jobs=user.max_concurrent_jobs,
            rate_limit_per_minute=user.rate_limit_per_minute,
        )
        self.session.add(user_model)
        await self.session.flush()
        return self._model_to_domain(user_model)
    
    def _model_to_domain(self, model: UserModel) -> User:
        """Convert database model to domain entity"""
        return User(
            id=model.id,
            api_key_hash=model.api_key_hash,
            name=model.name,
            max_concurrent_jobs=model.max_concurrent_jobs,
            rate_limit_per_minute=model.rate_limit_per_minute,
        )

