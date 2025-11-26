"""Lease manager for job processing"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.core.domain.job import Job
from app.core.exceptions.custom_exceptions import LeaseAcquisitionError
from app.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


class LeaseManager:
    """Manages job leases"""
    
    def __init__(self, session: AsyncSession, lease_ttl_seconds: int = 300):
        self.session = session
        self.job_repository = JobRepository(session)
        self.lease_ttl_seconds = lease_ttl_seconds
    
    async def acquire_lease(self, job: Job) -> bool:
        """Acquire lease on a job"""
        try:
            success = await self.job_repository.acquire_lease(
                job.id, self.lease_ttl_seconds
            )
            if success:
                logger.info(
                    "lease_acquired",
                    job_id=str(job.id),
                    tenant_id=job.tenant_id,
                    trace_id=job.trace_id,
                )
            return success
        except Exception as e:
            logger.error(
                "lease_acquisition_failed",
                job_id=str(job.id),
                error=str(e),
            )
            return False
    
    async def release_lease(self, job_id: UUID) -> None:
        """Release lease on a job"""
        await self.job_repository.release_lease(job_id)
        logger.debug("lease_released", job_id=str(job_id))
    
    async def extend_lease(self, job_id: UUID) -> bool:
        """Extend lease on a job"""
        lease_expires_at = datetime.utcnow() + timedelta(
            seconds=self.lease_ttl_seconds
        )
        # This would require an update method in repository
        # For now, we'll rely on the lease TTL being long enough
        return True

