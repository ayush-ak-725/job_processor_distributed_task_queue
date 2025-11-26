"""Job service for business logic"""

from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.job import Job
from app.core.domain.user import User
from app.core.domain.enums import JobStatus
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.infrastructure.queue.queue_strategy import QueueStrategy
from app.core.services.idempotency_service import IdempotencyService
from app.core.services.quota_service import QuotaService
from app.core.exceptions.custom_exceptions import (
    JobNotFoundError,
    JobAlreadyExistsError,
    QuotaExceededError,
)


class JobService:
    """Service for job business logic"""
    
    def __init__(
        self,
        session: AsyncSession,
        queue_strategy: QueueStrategy,
    ):
        self.session = session
        self.job_repository = JobRepository(session)
        self.queue_strategy = queue_strategy
        self.idempotency_service = IdempotencyService(session)
        self.quota_service = QuotaService(session)
    
    async def submit_job(
        self,
        user: User,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> Job:
        """Submit a new job"""
        # Check quota
        await self.quota_service.check_concurrent_jobs_limit(user)
        
        # Check idempotency
        if idempotency_key:
            existing_job = await self.idempotency_service.check_idempotency(
                user.id, idempotency_key
            )
            if existing_job:
                return existing_job
        
        # Create job
        job = Job(
            tenant_id=user.id,
            payload=payload,
            idempotency_key=idempotency_key,
            max_retries=max_retries,
        )
        
        # Enqueue job
        await self.queue_strategy.enqueue(job)
        
        return job
    
    async def get_job(self, job_id: UUID, tenant_id: Optional[str] = None) -> Job:
        """Get job by ID"""
        job = await self.job_repository.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        if tenant_id and job.tenant_id != tenant_id:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        return job
    
    async def get_jobs_by_status(
        self, status: JobStatus, tenant_id: Optional[str] = None, limit: int = 100
    ) -> list[Job]:
        """Get jobs by status"""
        return await self.job_repository.get_jobs_by_status(status, tenant_id, limit)
    
    async def get_dlq_jobs(
        self, tenant_id: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        """Get DLQ jobs"""
        return await self.job_repository.get_dlq_jobs(tenant_id, limit)

