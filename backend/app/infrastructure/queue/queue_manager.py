"""Queue manager"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.queue.queue_strategy import QueueStrategy
from app.infrastructure.queue.postgresql_queue import PostgreSQLQueueStrategy


class QueueManager:
    """Queue manager factory"""
    
    @staticmethod
    def create_queue_strategy(session: AsyncSession) -> QueueStrategy:
        """Create queue strategy instance"""
        return PostgreSQLQueueStrategy(session)

