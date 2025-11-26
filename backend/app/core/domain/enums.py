"""Domain enumerations"""

from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"  # Dead Letter Queue


class JobEvent(str, Enum):
    """Job event types for observability"""
    SUBMITTED = "submitted"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DLQ = "dlq"

