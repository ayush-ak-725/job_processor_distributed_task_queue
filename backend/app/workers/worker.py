"""Worker for processing jobs"""

import asyncio
from typing import Optional, Callable, Any, Dict
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.domain.job import Job
from app.core.domain.enums import JobStatus, JobEvent
from app.infrastructure.persistence.database import engine, AsyncSessionLocal
from app.infrastructure.persistence.repositories.job_repository import JobRepository
from app.infrastructure.queue.queue_strategy import QueueStrategy
from app.infrastructure.queue.queue_manager import QueueManager
from app.workers.lease_manager import LeaseManager
from app.infrastructure.observability.logger import get_logger
from app.infrastructure.observability.events import event_bus
from app.core.config import settings
from app.core.exceptions.custom_exceptions import JobNotFoundError

logger = get_logger(__name__)


class Worker:
    """Worker for processing jobs"""
    
    def __init__(
        self,
        worker_id: str,
        session: AsyncSession,
        queue_strategy: QueueStrategy,
        job_processor: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        self.worker_id = worker_id
        self.session = session
        self.queue_strategy = queue_strategy
        self.job_repository = JobRepository(session)
        self.lease_manager = LeaseManager(
            session, settings.WORKER_LEASE_TTL_SECONDS
        )
        self.job_processor = job_processor or self._default_job_processor
        self.running = False
    
    async def _default_job_processor(self, payload: Dict[str, Any]) -> Any:
        """Default job processor - simulates work"""
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Example: process payload
        if "error" in payload and payload["error"]:
            raise Exception(payload.get("error_message", "Job processing failed"))
        
        return {"result": "success", "processed": payload}
    
    async def process_job(self, job: Job) -> None:
        """Process a single job"""
        try:
            logger.info(
                "job_processing_started",
                job_id=str(job.id),
                tenant_id=job.tenant_id,
                worker_id=self.worker_id,
                trace_id=job.trace_id,
            )
            
            # Publish event
            await event_bus.publish(
                JobEvent.STARTED.value,
                {
                    "job_id": str(job.id),
                    "tenant_id": job.tenant_id,
                    "worker_id": self.worker_id,
                    "trace_id": job.trace_id,
                },
            )
            
            # Process job
            result = await self.job_processor(job.payload)
            
            # Mark as completed
            await self.job_repository.update_status(job.id, JobStatus.COMPLETED)
            
            logger.info(
                "job_processing_completed",
                job_id=str(job.id),
                tenant_id=job.tenant_id,
                worker_id=self.worker_id,
                trace_id=job.trace_id,
                result=result,
            )
            
            # Publish event
            await event_bus.publish(
                JobEvent.COMPLETED.value,
                {
                    "job_id": str(job.id),
                    "tenant_id": job.tenant_id,
                    "worker_id": self.worker_id,
                    "trace_id": job.trace_id,
                    "result": result,
                },
            )
        
        except Exception as e:
            error_message = str(e)
            logger.error(
                "job_processing_failed",
                job_id=str(job.id),
                tenant_id=job.tenant_id,
                worker_id=self.worker_id,
                trace_id=job.trace_id,
                error=error_message,
            )
            
            # Update job status
            await self.job_repository.update_status(
                job.id, JobStatus.FAILED, error_message
            )
            
            # Check if should retry
            job = await self.job_repository.get_by_id(job.id)
            if job and job.can_retry():
                # Retry
                await self.job_repository.increment_retry(job.id)
                
                logger.info(
                    "job_retry_scheduled",
                    job_id=str(job.id),
                    retry_count=job.retry_count + 1,
                    max_retries=job.max_retries,
                    trace_id=job.trace_id,
                )
                
                await event_bus.publish(
                    JobEvent.RETRY.value,
                    {
                        "job_id": str(job.id),
                        "tenant_id": job.tenant_id,
                        "retry_count": job.retry_count,
                        "trace_id": job.trace_id,
                    },
                )
            else:
                # Move to DLQ
                if job:
                    await self.job_repository.move_to_dlq(job, error_message)
                    
                    logger.warning(
                        "job_moved_to_dlq",
                        job_id=str(job.id),
                        tenant_id=job.tenant_id,
                        retry_count=job.retry_count,
                        trace_id=job.trace_id,
                    )
                    
                    await event_bus.publish(
                        JobEvent.DLQ.value,
                        {
                            "job_id": str(job.id),
                            "tenant_id": job.tenant_id,
                            "error_message": error_message,
                            "trace_id": job.trace_id,
                        },
                    )
            
            # Publish failure event
            await event_bus.publish(
                JobEvent.FAILED.value,
                {
                    "job_id": str(job.id) if job else "unknown",
                    "tenant_id": job.tenant_id if job else "unknown",
                    "worker_id": self.worker_id,
                    "error": error_message,
                    "trace_id": job.trace_id if job else "unknown",
                },
            )
    
    async def run_once(self) -> bool:
        """Run one iteration of job processing"""
        try:
            # Dequeue job
            job = await self.queue_strategy.dequeue(self.worker_id)
            
            if job is None:
                return False
            
            # Try to acquire lease
            lease_acquired = await self.lease_manager.acquire_lease(job)
            
            if not lease_acquired:
                logger.debug(
                    "lease_not_acquired",
                    job_id=str(job.id),
                    worker_id=self.worker_id,
                )
                return False
            
            # Process job
            await self.process_job(job)
            
            return True
        
        except Exception as e:
            logger.error(
                "worker_error",
                worker_id=self.worker_id,
                error=str(e),
            )
            return False
    
    async def start(self) -> None:
        """Start worker loop"""
        self.running = True
        logger.info("worker_started", worker_id=self.worker_id)
        
        while self.running:
            try:
                processed = await self.run_once()
                
                if not processed:
                    # No jobs available, wait before polling again
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            
            except asyncio.CancelledError:
                logger.info("worker_cancelled", worker_id=self.worker_id)
                break
            except Exception as e:
                logger.error(
                    "worker_loop_error",
                    worker_id=self.worker_id,
                    error=str(e),
                )
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
    
    async def stop(self) -> None:
        """Stop worker"""
        self.running = False
        logger.info("worker_stopped", worker_id=self.worker_id)


class WorkerManager:
    """Manages worker pool"""
    
    def __init__(self, pool_size: int = None):
        self.pool_size = pool_size or settings.WORKER_POOL_SIZE
        self.workers: list[Worker] = []
        self.tasks: list[asyncio.Task] = []
    
    async def start_workers(self, job_processor: Optional[Callable] = None) -> None:
        """Start worker pool"""
        logger.info(
            "worker_pool_starting",
            pool_size=self.pool_size,
        )
        
        for i in range(self.pool_size):
            worker_id = f"worker-{i+1}"
            session = AsyncSessionLocal()
            queue_strategy = QueueManager.create_queue_strategy(session)
            
            worker = Worker(worker_id, session, queue_strategy, job_processor)
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.start())
            self.tasks.append(task)
        
        logger.info("worker_pool_started", pool_size=self.pool_size)
    
    async def stop_workers(self) -> None:
        """Stop all workers"""
        logger.info("worker_pool_stopping")
        
        for worker in self.workers:
            await worker.stop()
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("worker_pool_stopped")

