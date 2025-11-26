# Database Setup Guide

## External Database Configuration

You're using an external PostgreSQL database on Render.com. Here's how to set it up:

## Database URL Format

Your database URL is:
```
postgresql://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue
```

**Important**: For async operations in SQLAlchemy, we need to use `postgresql+asyncpg://` instead of `postgresql://`.

The application automatically handles this conversion, but you should use:
```
postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue
```

## Setup Steps

### 1. Set Environment Variable

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue
SECRET_KEY=your-secret-key-here
EOF
```

### 2. Run Database Migrations

Since you're using an external database, you should use Alembic migrations instead of `create_all()`:

```bash
# From the backend directory
cd backend

# Run migrations to create all tables
alembic upgrade head
```

This will create all the necessary tables:
- `users` - User/tenant information
- `jobs` - Job queue
- `dlq` - Dead Letter Queue
- `metrics` - Metrics storage

### 3. Verify Connection

Test the database connection:

```bash
# Using Python
python -c "
import asyncio
from app.infrastructure.persistence.database import engine

async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('✅ Database connection successful!')
    await engine.dispose()

asyncio.run(test())
"
```

### 4. Create Initial User

Create a test user:

```bash
python scripts/create_user.py tenant1 my-api-key-123
```

## Docker Configuration

When using Docker, set the `DATABASE_URL` environment variable:

```bash
# In docker-compose files, it's already configured
# Or set it manually:
export DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue

docker-compose up -d
```

## Important Notes

### 1. Alembic vs create_all()

- **Development**: `create_all()` in `main.py` is fine for quick testing
- **Production**: Always use Alembic migrations for external databases
- **Why**: External databases shouldn't be dropped/recreated, and migrations provide version control

### 2. Connection String Format

- **For Application (async)**: `postgresql+asyncpg://...`
- **For Alembic (sync)**: `postgresql://...` (automatically converted)

### 3. SSL Connection (if required)

If your Render.com database requires SSL, you may need to add SSL parameters:

```python
DATABASE_URL = "postgresql+asyncpg://user:pass@host/db?sslmode=require"
```

### 4. Connection Pooling

The application uses SQLAlchemy connection pooling. For external databases:
- Default pool size: 10
- Max overflow: 20
- Pool pre-ping: Enabled (checks connections before use)

## Troubleshooting

### Connection Refused
- Check if the database URL is correct
- Verify network access to Render.com
- Check firewall settings

### SSL Required
- Add `?sslmode=require` to the connection string
- Or configure SSL in SQLAlchemy engine

### Migration Errors
- Make sure you're running migrations from the `backend/` directory
- Check that `alembic.ini` has the correct database URL
- Verify database user has CREATE TABLE permissions

### Tables Already Exist
- If tables exist, migrations will skip creating them
- To reset: Drop tables manually, then run `alembic upgrade head`

## Running Migrations in Docker

```bash
# Run migrations in backend container
docker-compose exec backend alembic upgrade head

# Or using the script
docker-compose exec backend python scripts/run_migrations.py
```

