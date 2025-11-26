"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('api_key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('max_concurrent_jobs', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Index('ix_users_api_key_hash', 'api_key_hash'),
    )
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('payload', postgresql.JSON(), nullable=False),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(), nullable=True),
        sa.Column('trace_id', sa.String(255), nullable=False),
        sa.Index('ix_jobs_tenant_id', 'tenant_id'),
        sa.Index('ix_jobs_status', 'status'),
        sa.Index('ix_jobs_idempotency_key', 'idempotency_key'),
        sa.Index('ix_jobs_created_at', 'created_at'),
        sa.Index('ix_jobs_lease_expires_at', 'lease_expires_at'),
        sa.Index('idx_jobs_status_created', 'status', 'created_at'),
        sa.Index('idx_jobs_tenant_idempotency', 'tenant_id', 'idempotency_key'),
    )
    
    # Create DLQ table
    op.create_table(
        'dlq',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('original_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('failed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('trace_id', sa.String(255), nullable=False),
        sa.Index('ix_dlq_original_job_id', 'original_job_id'),
        sa.Index('ix_dlq_tenant_id', 'tenant_id'),
        sa.Index('ix_dlq_failed_at', 'failed_at'),
    )
    
    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('total_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('running_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dlq_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Index('ix_metrics_timestamp', 'timestamp'),
    )


def downgrade() -> None:
    op.drop_table('metrics')
    op.drop_table('dlq')
    op.drop_table('jobs')
    op.drop_table('users')

