# 🚀 Quick Start Guide

## Using External Database (Render.com)

Your database is already configured! Here's how to get started:

### 1. Set Environment Variable

```bash
export DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue
```

Or create a `.env` file in the `backend/` directory:
```bash
cd backend
echo "DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue" > .env
```

### 2. Run Database Migrations

Create all tables in your external database:

```bash
cd backend
alembic upgrade head
```

This creates:
- `users` table
- `jobs` table  
- `dlq` table
- `metrics` table

### 3. Create a Test User

```bash
cd backend
python scripts/create_user.py tenant1 my-api-key-123
```

### 4. Start the Application

#### Option A: Using Docker (Recommended)

```bash
# Set environment variable
export DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue

# Start services (without local postgres)
docker-compose -f docker-compose.prod.yml up -d

# Or for development
docker-compose -f docker-compose.dev.yml up -d
```

#### Option B: Manual Start

```bash
# Terminal 1: Start API
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Workers
cd backend
python scripts/run_worker.py

# Terminal 3: Start Frontend
cd frontend
npm install
npm run dev
```

### 5. Access the Dashboard

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6. Test It!

1. Open http://localhost:3000
2. Enter API key: `my-api-key-123`
3. Submit a test job:
   ```json
   {
     "task": "test",
     "data": {"message": "Hello World"}
   }
   ```
4. Watch it process in real-time!

## What is Alembic?

**Alembic** is a database migration tool. It's like Git for your database schema.

- ✅ Tracks all database changes
- ✅ Can rollback changes
- ✅ Version controlled
- ✅ Team collaboration

**Why use it?**
- For external databases, you can't use `create_all()` safely
- Migrations provide controlled, tested schema changes
- Production best practice

See [ALEMBIC_EXPLANATION.md](ALEMBIC_EXPLANATION.md) for more details.

## Troubleshooting

### "Connection refused" error
- Check your database URL is correct
- Verify network access to Render.com
- Make sure the database is running

### "Table already exists" error
- Tables might already exist
- Run `alembic upgrade head` - it will skip existing tables
- Or check existing tables: `alembic current`

### "No module named 'app'" error
- Make sure you're in the `backend/` directory
- Or set `PYTHONPATH=backend`

## Next Steps

- Read [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed database configuration
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Check [README.md](README.md) for full documentation

