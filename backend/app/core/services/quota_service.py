"""Quota service for managing tenant quotas"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.core.exceptions.custom_exceptions import QuotaExceededError


class QuotaService:
    """Service for managing tenant quotas"""
    
    def __init__(self, session: AsyncSession):
        self.job_repository = JobRepository(session)
    
    async def check_concurrent_jobs_limit(self, user: User) -> None:
        """Check if user has exceeded concurrent jobs limit"""
        running_jobs_count = await self.job_repository.count_running_jobs(user.id)
        
        if running_jobs_count >= user.max_concurrent_jobs:
            raise QuotaExceededError(
                f"Concurrent jobs limit exceeded. "
                f"Current: {running_jobs_count}, Limit: {user.max_concurrent_jobs}"
            )
    
    async def get_concurrent_jobs_count(self, tenant_id: str) -> int:
        """Get current concurrent jobs count for a tenant"""
        return await self.job_repository.count_running_jobs(tenant_id)

