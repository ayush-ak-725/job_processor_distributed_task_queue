"""Custom exception classes"""


class JobProcessorException(Exception):
    """Base exception for job processor"""
    pass


class JobNotFoundError(JobProcessorException):
    """Job not found"""
    pass


class JobAlreadyExistsError(JobProcessorException):
    """Job with same idempotency key already exists"""
    pass


class QuotaExceededError(JobProcessorException):
    """Tenant quota exceeded"""
    pass


class RateLimitExceededError(JobProcessorException):
    """Rate limit exceeded"""
    pass


class LeaseAcquisitionError(JobProcessorException):
    """Failed to acquire lease on job"""
    pass


class InvalidJobStatusError(JobProcessorException):
    """Invalid job status transition"""
    pass

