"""PostgreSQL-based queue implementation"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.job import Job
from app.core.domain.enums import JobStatus
from app.infrastructure.queue.queue_strategy import QueueStrategy
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.core.exceptions.custom_exceptions import JobNotFoundError


class PostgreSQLQueueStrategy(QueueStrategy):
    """PostgreSQL-based queue implementation using SELECT FOR UPDATE SKIP LOCKED"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repository = JobRepository(session)
    
    async def enqueue(self, job: Job) -> None:
        """Enqueue a job by creating it in the database"""
        await self.job_repository.create(job)
    
    async def dequeue(self, worker_id: str) -> Optional[Job]:
        """Dequeue a job using SELECT FOR UPDATE SKIP LOCKED"""
        jobs = await self.job_repository.get_pending_jobs_for_dequeue(limit=1)
        if not jobs:
            return None
        return jobs[0]
    
    async def lease(self, job_id: str, ttl_seconds: int) -> bool:
        """Acquire lease on a job atomically"""
        try:
            job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
            return await self.job_repository.acquire_lease(job_uuid, ttl_seconds)
        except ValueError:
            return False
    
    async def ack(self, job_id: str, success: bool, error_message: Optional[str] = None) -> None:
        """Acknowledge job completion"""
        try:
            job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
            if success:
                await self.job_repository.update_status(job_uuid, JobStatus.COMPLETED)
            else:
                await self.job_repository.update_status(
                    job_uuid, JobStatus.FAILED, error_message
                )
        except JobNotFoundError:
            pass  # Job already processed or doesn't exist

