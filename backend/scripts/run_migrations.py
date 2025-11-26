"""Script to run Alembic migrations"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


def run_migrations():
    """Run Alembic migrations"""
    import subprocess
    
    logger.info("running_migrations", database_url=settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden")
    
    # Run alembic upgrade head
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        logger.info("migrations_completed_successfully")
        print(result.stdout)
    else:
        logger.error("migrations_failed", error=result.stderr)
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()

