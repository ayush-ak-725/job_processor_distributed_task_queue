"""Queue strategy interface"""

from abc import ABC, abstractmethod
from typing import Optional

from app.core.domain.job import Job


class QueueStrategy(ABC):
    """Abstract queue strategy interface"""
    
    @abstractmethod
    async def enqueue(self, job: Job) -> None:
        """Enqueue a job"""
        pass
    
    @abstractmethod
    async def dequeue(self, worker_id: str) -> Optional[Job]:
        """Dequeue a job for processing"""
        pass
    
    @abstractmethod
    async def lease(self, job_id: str, ttl_seconds: int) -> bool:
        """Acquire lease on a job"""
        pass
    
    @abstractmethod
    async def ack(self, job_id: str, success: bool, error_message: Optional[str] = None) -> None:
        """Acknowledge job completion"""
        pass

