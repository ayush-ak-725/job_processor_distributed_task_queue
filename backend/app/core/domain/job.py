"""Job domain entity"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from app.core.domain.enums import JobStatus


class Job:
    """Job domain entity representing a task to be processed"""
    
    def __init__(
        self,
        tenant_id: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
        job_id: Optional[UUID] = None,
        status: JobStatus = JobStatus.PENDING,
        retry_count: int = 0,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        lease_expires_at: Optional[datetime] = None,
        trace_id: Optional[str] = None,
    ):
        self.id = job_id or uuid4()
        self.tenant_id = tenant_id
        self.payload = payload
        self.idempotency_key = idempotency_key
        self.status = status
        self.max_retries = max_retries
        self.retry_count = retry_count
        self.created_at = created_at or datetime.utcnow()
        self.started_at = started_at
        self.completed_at = completed_at
        self.error_message = error_message
        self.lease_expires_at = lease_expires_at
        self.trace_id = trace_id or str(uuid4())
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries
    
    def should_move_to_dlq(self) -> bool:
        """Check if job should be moved to DLQ"""
        return self.status == JobStatus.FAILED and not self.can_retry()
    
    def is_lease_expired(self) -> bool:
        """Check if lease has expired"""
        if self.lease_expires_at is None:
            return False
        return datetime.utcnow() > self.lease_expires_at
    
    def __repr__(self) -> str:
        return (
            f"Job(id={self.id}, tenant_id={self.tenant_id}, "
            f"status={self.status.value}, retry_count={self.retry_count})"
        )

