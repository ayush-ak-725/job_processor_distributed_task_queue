"""Alembic environment configuration"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio

# Import your models
# Note: We import Base directly to avoid loading async engine
from app.infrastructure.persistence.models.job_model import (
    JobModel,
    UserModel,
    DLQModel,
    MetricsModel,
)
from app.core.config import settings

# Import Base after models are imported
from app.infrastructure.persistence.database import Base

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url with settings
# Alembic uses synchronous SQLAlchemy, so we need to convert asyncpg URL to psycopg2
# Convert postgresql+asyncpg:// to postgresql:// for Alembic
alembic_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", alembic_db_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

