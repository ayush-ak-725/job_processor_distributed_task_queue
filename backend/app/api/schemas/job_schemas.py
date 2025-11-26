"""Job API schemas"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    """Request schema for creating a job"""
    payload: Dict[str, Any] = Field(..., description="Job payload")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retries")


class JobResponse(BaseModel):
    """Response schema for job"""
    id: UUID
    tenant_id: str
    status: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str]
    max_retries: int
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    trace_id: str
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response schema for job list"""
    jobs: list[JobResponse]
    total: int


class DLQJobResponse(BaseModel):
    """Response schema for DLQ job"""
    id: str
    original_job_id: str
    tenant_id: str
    payload: Dict[str, Any]
    error_message: Optional[str]
    retry_count: int
    failed_at: str
    trace_id: str


class MetricsResponse(BaseModel):
    """Response schema for metrics"""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    dlq_jobs: int

