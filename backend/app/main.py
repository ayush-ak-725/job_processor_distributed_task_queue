"""FastAPI application entry point"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs, health, websocket
from app.api.middleware.rate_limit_middleware import RateLimitMiddleware
from app.infrastructure.persistence.database import engine, Base
from app.infrastructure.observability.logger import get_logger
from app.core.config import settings

from app.workers.worker import WorkerManager

logger = get_logger(__name__)

# Initialize worker manager
worker_manager = WorkerManager(pool_size=settings.WORKER_POOL_SIZE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""

    # ---------------------- STARTUP ----------------------
    logger.info("application_starting", port=settings.API_PORT)

    # Create DB tables (dev only)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("tables_created_or_existing")
    except Exception as e:
        logger.warning("table_creation_skipped", error=str(e))
        logger.info("using_existing_tables_or_run_migrations")

    # 🚀 START WORKERS
    try:
        await worker_manager.start_workers()
        logger.info("worker_pool_started", pool_size=settings.WORKER_POOL_SIZE)
    except Exception as e:
        logger.error("worker_pool_failed_to_start", error=str(e))

    logger.info("application_started")

    # Yield control back to FastAPI
    yield

    # ---------------------- SHUTDOWN ----------------------
    logger.info("application_shutting_down")

    # 🚦 STOP WORKERS
    try:
        await worker_manager.stop_workers()
        logger.info("worker_pool_stopped")
    except Exception as e:
        logger.error("failed_to_stop_worker_pool", error=str(e))

    # Close DB engine
    await engine.dispose()


app = FastAPI(
    title="Distributed Task Queue & Job Processor",
    description="A small-scale distributed job queue and worker system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {
        "message": "Distributed Task Queue & Job Processor API",
        "version": "1.0.0",
        "docs": "/docs",
    }
