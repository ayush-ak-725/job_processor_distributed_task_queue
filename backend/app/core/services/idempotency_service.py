"""Idempotency service"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.job import Job
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.core.exceptions.custom_exceptions import JobAlreadyExistsError


class IdempotencyService:
    """Service for handling job idempotency"""
    
    def __init__(self, session: AsyncSession):
        self.job_repository = JobRepository(session)
    
    async def check_idempotency(
        self, tenant_id: str, idempotency_key: Optional[str]
    ) -> Optional[Job]:
        """Check if job with idempotency key already exists"""
        if not idempotency_key:
            return None
        
        existing_job = await self.job_repository.get_by_idempotency_key(
            tenant_id, idempotency_key
        )
        return existing_job
    
    async def validate_and_get_existing(
        self, tenant_id: str, idempotency_key: Optional[str]
    ) -> Optional[Job]:
        """Validate idempotency and return existing job if found"""
        if not idempotency_key:
            return None
        
        existing_job = await self.check_idempotency(tenant_id, idempotency_key)
        if existing_job:
            return existing_job
        
        return None

