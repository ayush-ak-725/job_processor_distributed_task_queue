"""Metrics collector"""

from typing import Dict, Optional
from datetime import datetime
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.core.domain.enums import JobStatus


class MetricsCollector:
    """Metrics collector using Observer pattern"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repository = JobRepository(session)
        self._observers: list = []
    
    def attach(self, observer) -> None:
        """Attach observer"""
        self._observers.append(observer)
    
    def detach(self, observer) -> None:
        """Detach observer"""
        self._observers.remove(observer)
    
    def notify(self, event: str, data: Dict) -> None:
        """Notify all observers"""
        for observer in self._observers:
            observer.update(event, data)
    
    async def get_metrics(
        self, tenant_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Get current metrics"""
        metrics = {
            "total_jobs": await self.job_repository.count_by_status(
                JobStatus.PENDING, tenant_id
            ) + await self.job_repository.count_by_status(
                JobStatus.RUNNING, tenant_id
            ) + await self.job_repository.count_by_status(
                JobStatus.COMPLETED, tenant_id
            ) + await self.job_repository.count_by_status(
                JobStatus.FAILED, tenant_id
            ) + await self.job_repository.count_by_status(
                JobStatus.DLQ, tenant_id
            ),
            "pending_jobs": await self.job_repository.count_by_status(
                JobStatus.PENDING, tenant_id
            ),
            "running_jobs": await self.job_repository.count_by_status(
                JobStatus.RUNNING, tenant_id
            ),
            "completed_jobs": await self.job_repository.count_by_status(
                JobStatus.COMPLETED, tenant_id
            ),
            "failed_jobs": await self.job_repository.count_by_status(
                JobStatus.FAILED, tenant_id
            ),
            "dlq_jobs": await self.job_repository.count_by_status(
                JobStatus.DLQ, tenant_id
            ),
        }
        
        # Notify observers
        self.notify("metrics_updated", metrics)
        
        return metrics


class MetricsObserver:
    """Observer interface for metrics"""
    
    def update(self, event: str, data: Dict) -> None:
        """Update observer with new data"""
        pass

