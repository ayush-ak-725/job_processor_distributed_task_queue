"""Job API routes"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.job_schemas import (
    JobCreateRequest,
    JobResponse,
    JobListResponse,
    DLQJobResponse,
    MetricsResponse,
)
from app.api.middleware.auth_middleware import get_current_user
from app.infrastructure.persistence.database import get_db
from app.core.domain.user import User
from app.core.domain.enums import JobStatus
from app.core.services.job_service import JobService
from app.infrastructure.queue.queue_manager import QueueManager
from app.infrastructure.observability.metrics import MetricsCollector
from app.infrastructure.observability.logger import get_logger
from app.infrastructure.observability.events import event_bus
from app.core.exceptions.custom_exceptions import (
    JobNotFoundError,
    JobAlreadyExistsError,
    QuotaExceededError,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
logger = get_logger(__name__)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_request: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new job"""
    try:
        queue_strategy = QueueManager.create_queue_strategy(db)
        job_service = JobService(db, queue_strategy)
        
        job = await job_service.submit_job(
            user=current_user,
            payload=job_request.payload,
            idempotency_key=job_request.idempotency_key,
            max_retries=job_request.max_retries,
        )
        
        # Log event
        logger.info(
            "job_submitted",
            job_id=str(job.id),
            tenant_id=job.tenant_id,
            trace_id=job.trace_id,
        )
        
        # Publish event
        await event_bus.publish(
            "job_submitted",
            {
                "job_id": str(job.id),
                "tenant_id": job.tenant_id,
                "status": job.status.value,
                "trace_id": job.trace_id,
            },
        )
        
        return JobResponse(
            id=job.id,
            tenant_id=job.tenant_id,
            status=job.status.value,
            payload=job.payload,
            idempotency_key=job.idempotency_key,
            max_retries=job.max_retries,
            retry_count=job.retry_count,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            trace_id=job.trace_id,
        )
    except JobAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get job by ID"""
    try:
        queue_strategy = QueueManager.create_queue_strategy(db)
        job_service = JobService(db, queue_strategy)
        
        job = await job_service.get_job(job_id, current_user.id)
        
        return JobResponse(
            id=job.id,
            tenant_id=job.tenant_id,
            status=job.status.value,
            payload=job.payload,
            idempotency_key=job.idempotency_key,
            max_retries=job.max_retries,
            retry_count=job.retry_count,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            trace_id=job.trace_id,
        )
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    """List jobs"""
    queue_strategy = QueueManager.create_queue_strategy(db)
    job_service = JobService(db, queue_strategy)
    
    if status:
        jobs = await job_service.get_jobs_by_status(
            status, current_user.id, limit
        )
    else:
        # Get all jobs for user
        all_jobs = []
        for job_status in JobStatus:
            status_jobs = await job_service.get_jobs_by_status(
                job_status, current_user.id, limit
            )
            all_jobs.extend(status_jobs)
        jobs = all_jobs[:limit]
    
    return JobListResponse(
        jobs=[
            JobResponse(
                id=job.id,
                tenant_id=job.tenant_id,
                status=job.status.value,
                payload=job.payload,
                idempotency_key=job.idempotency_key,
                max_retries=job.max_retries,
                retry_count=job.retry_count,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
                trace_id=job.trace_id,
            )
            for job in jobs
        ],
        total=len(jobs),
    )


@router.get("/dlq", response_model=list[DLQJobResponse])
async def get_dlq_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    """Get Dead Letter Queue jobs"""
    queue_strategy = QueueManager.create_queue_strategy(db)
    job_service = JobService(db, queue_strategy)
    
    dlq_jobs = await job_service.get_dlq_jobs(current_user.id, limit)
    
    return [
        DLQJobResponse(**job) for job in dlq_jobs
    ]


@router.get("/metrics/summary", response_model=MetricsResponse)
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get job metrics"""
    metrics_collector = MetricsCollector(db)
    metrics = await metrics_collector.get_metrics(current_user.id)
    
    return MetricsResponse(**metrics)

