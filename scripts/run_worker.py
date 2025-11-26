"""Script to run worker pool"""

import asyncio
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers.worker import WorkerManager
from app.core.config import settings
from app.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Main worker process"""
    worker_manager = WorkerManager(pool_size=settings.WORKER_POOL_SIZE)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("shutdown_signal_received")
        asyncio.create_task(worker_manager.stop_workers())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker_manager.start_workers()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    finally:
        await worker_manager.stop_workers()
        logger.info("worker_process_exiting")


if __name__ == "__main__":
    asyncio.run(main())

