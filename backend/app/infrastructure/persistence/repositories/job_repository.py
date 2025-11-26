"""Job repository implementation"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.job import Job
from app.core.domain.enums import JobStatus
from app.infrastructure.persistence.models.job_model import JobModel, DLQModel
from app.core.exceptions.custom_exceptions import JobNotFoundError


class JobRepository:
    """Repository for job data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, job: Job) -> Job:
        job_model = JobModel(
            id=job.id,
            tenant_id=job.tenant_id,
            status=job.status.value,
            payload=job.payload,
            idempotency_key=job.idempotency_key,
            max_retries=job.max_retries,
            retry_count=job.retry_count,
            created_at=job.created_at,
            trace_id=job.trace_id,
        )
        self.session.add(job_model)
        await self.session.commit()                      # <-- FIX
        return self._model_to_domain(job_model)
    
    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        result = await self.session.execute(
            select(JobModel).where(JobModel.id == job_id)
        )
        job_model = result.scalar_one_or_none()
        return None if job_model is None else self._model_to_domain(job_model)
    
    async def get_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> Optional[Job]:
        result = await self.session.execute(
            select(JobModel).where(
                and_(
                    JobModel.tenant_id == tenant_id,
                    JobModel.idempotency_key == idempotency_key,
                )
            )
        )
        job_model = result.scalar_one_or_none()
        return None if job_model is None else self._model_to_domain(job_model)
    
    async def update_status(self, job_id: UUID, status: JobStatus, error_message: Optional[str] = None) -> Job:
        update_data = {"status": status.value}

        if error_message:
            update_data["error_message"] = error_message
        
        if status == JobStatus.RUNNING:
            update_data["started_at"] = datetime.utcnow()
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DLQ):
            update_data["completed_at"] = datetime.utcnow()
        
        await self.session.execute(
            update(JobModel)
            .where(JobModel.id == job_id)
            .values(**update_data)
        )
        await self.session.commit()                     # <-- FIX
        
        job = await self.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job
    
    async def acquire_lease(self, job_id: UUID, lease_ttl_seconds: int) -> bool:
        lease_expires_at = datetime.utcnow() + timedelta(seconds=lease_ttl_seconds)
        
        result = await self.session.execute(
            update(JobModel)
            .where(
                and_(
                    JobModel.id == job_id,
                    JobModel.status == JobStatus.PENDING.value,
                    or_(
                        JobModel.lease_expires_at.is_(None),
                        JobModel.lease_expires_at < datetime.utcnow(),
                    ),
                )
            )
            .values(
                status=JobStatus.RUNNING.value,
                lease_expires_at=lease_expires_at,
                started_at=datetime.utcnow(),
            )
        )
        await self.session.commit()                    # <-- FIX
        return result.rowcount > 0
    
    async def release_lease(self, job_id: UUID) -> None:
        await self.session.execute(
            update(JobModel)
            .where(JobModel.id == job_id)
            .values(lease_expires_at=None)
        )
        await self.session.commit()                    # <-- FIX
    
    async def increment_retry(self, job_id: UUID) -> Job:
        await self.session.execute(
            update(JobModel)
            .where(JobModel.id == job_id)
            .values(
                retry_count=JobModel.retry_count + 1,
                status=JobStatus.PENDING.value,
                lease_expires_at=None,
                started_at=None,
                error_message=None,
            )
        )
        await self.session.commit()                    # <-- FIX
        
        job = await self.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job
    
    async def get_pending_jobs_for_dequeue(self, limit: int = 1) -> List[Job]:
        result = await self.session.execute(
            select(JobModel)
            .where(
                and_(
                    JobModel.status == JobStatus.PENDING.value,
                    or_(
                        JobModel.lease_expires_at.is_(None),
                        JobModel.lease_expires_at < datetime.utcnow(),
                    ),
                )
            )
            .order_by(JobModel.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        job_models = result.scalars().all()
        return [self._model_to_domain(model) for model in job_models]
    
    async def get_jobs_by_status(self, status: JobStatus, tenant_id: Optional[str] = None, limit: int = 100) -> List[Job]:
        query = select(JobModel).where(JobModel.status == status.value)
        if tenant_id:
            query = query.where(JobModel.tenant_id == tenant_id)
        query = query.order_by(JobModel.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._model_to_domain(m) for m in models]
    
    async def count_by_status(self, status: JobStatus, tenant_id: Optional[str] = None) -> int:
        query = select(func.count(JobModel.id)).where(JobModel.status == status.value)
        if tenant_id:
            query = query.where(JobModel.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def count_running_jobs(self, tenant_id: str) -> int:
        return await self.count_by_status(JobStatus.RUNNING, tenant_id)
    
    async def move_to_dlq(self, job: Job, error_message: str) -> None:
        dlq_model = DLQModel(
            original_job_id=job.id,
            tenant_id=job.tenant_id,
            payload=job.payload,
            error_message=error_message,
            retry_count=job.retry_count,
            trace_id=job.trace_id,
        )
        
        self.session.add(dlq_model)
        await self.update_status(job.id, JobStatus.DLQ, error_message)
        await self.session.commit()                    # <-- FIX
    
    async def get_dlq_jobs(self, tenant_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        query = select(DLQModel)
        if tenant_id:
            query = query.where(DLQModel.tenant_id == tenant_id)
        query = query.order_by(DLQModel.failed_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        dlq_models = result.scalars().all()
        return [
            {
                "id": str(model.id),
                "original_job_id": str(model.original_job_id),
                "tenant_id": model.tenant_id,
                "payload": model.payload,
                "error_message": model.error_message,
                "retry_count": model.retry_count,
                "failed_at": model.failed_at.isoformat(),
                "trace_id": model.trace_id,
            }
            for model in dlq_models
        ]
    
    def _model_to_domain(self, model: JobModel) -> Job:
        return Job(
            job_id=model.id,
            tenant_id=model.tenant_id,
            payload=model.payload,
            idempotency_key=model.idempotency_key,
            max_retries=model.max_retries,
            status=JobStatus(model.status),
            retry_count=model.retry_count,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            lease_expires_at=model.lease_expires_at,
            trace_id=model.trace_id,
        )
