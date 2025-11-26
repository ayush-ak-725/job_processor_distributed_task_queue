"""Tests for job service"""

import pytest
from uuid import uuid4

from app.core.domain.job import Job
from app.core.domain.user import User
from app.core.domain.enums import JobStatus
from app.core.services.job_service import JobService
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.infrastructure.queue.postgresql_queue import PostgreSQLQueueStrategy
from app.core.exceptions.custom_exceptions import QuotaExceededError


@pytest.mark.asyncio
async def test_submit_job(test_session):
    """Test job submission"""
    user = User(
        id="test-tenant",
        api_key_hash="test-key",
        max_concurrent_jobs=5,
        rate_limit_per_minute=10,
    )
    
    queue_strategy = PostgreSQLQueueStrategy(test_session)
    job_service = JobService(test_session, queue_strategy)
    
    job = await job_service.submit_job(
        user=user,
        payload={"task": "test", "data": {}},
        max_retries=3,
    )
    
    assert job is not None
    assert job.status == JobStatus.PENDING
    assert job.tenant_id == user.id
    assert job.payload == {"task": "test", "data": {}}


@pytest.mark.asyncio
async def test_get_job(test_session):
    """Test getting a job"""
    user = User(
        id="test-tenant",
        api_key_hash="test-key",
        max_concurrent_jobs=5,
        rate_limit_per_minute=10,
    )
    
    queue_strategy = PostgreSQLQueueStrategy(test_session)
    job_service = JobService(test_session, queue_strategy)
    
    # Create a job
    job = await job_service.submit_job(
        user=user,
        payload={"task": "test"},
    )
    
    # Get the job
    retrieved_job = await job_service.get_job(job.id)
    
    assert retrieved_job.id == job.id
    assert retrieved_job.tenant_id == job.tenant_id

