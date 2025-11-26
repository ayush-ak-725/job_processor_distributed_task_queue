"""Job database model"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, DateTime, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.infrastructure.persistence.database import Base
from app.core.domain.enums import JobStatus


class JobModel(Base):
    """Job database model"""
    
    __tablename__ = "jobs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=JobStatus.PENDING.value, index=True)
    payload = Column(JSON, nullable=False)
    idempotency_key = Column(String(255), nullable=True, index=True)
    max_retries = Column(Integer, nullable=False, default=3)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True, index=True)
    trace_id = Column(String(255), nullable=False, default=lambda: str(uuid4()), index=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_tenant_idempotency', 'tenant_id', 'idempotency_key'),
        Index('idx_jobs_lease_expires', 'lease_expires_at'),
    )
    
    def __repr__(self) -> str:
        return f"JobModel(id={self.id}, tenant_id={self.tenant_id}, status={self.status})"


class UserModel(Base):
    """User/Tenant database model"""
    
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)
    api_key_hash = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)
    max_concurrent_jobs = Column(Integer, nullable=False, default=5)
    rate_limit_per_minute = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"UserModel(id={self.id}, name={self.name})"


class DLQModel(Base):
    """Dead Letter Queue database model"""
    
    __tablename__ = "dlq"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    original_job_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False)
    failed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    trace_id = Column(String(255), nullable=False)
    
    def __repr__(self) -> str:
        return f"DLQModel(id={self.id}, original_job_id={self.original_job_id})"


class MetricsModel(Base):
    """Metrics database model for storing aggregated metrics"""
    
    __tablename__ = "metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    total_jobs = Column(Integer, nullable=False, default=0)
    pending_jobs = Column(Integer, nullable=False, default=0)
    running_jobs = Column(Integer, nullable=False, default=0)
    completed_jobs = Column(Integer, nullable=False, default=0)
    failed_jobs = Column(Integer, nullable=False, default=0)
    dlq_jobs = Column(Integer, nullable=False, default=0)
    
    def __repr__(self) -> str:
        return f"MetricsModel(timestamp={self.timestamp})"

