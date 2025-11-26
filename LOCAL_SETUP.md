# 🏃 Local Development Setup

This guide will help you run and test the backend and frontend services locally.

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ installed
- PostgreSQL access (your external Render.com database)
- pip and npm available

## Step 1: Backend Setup

### 1.1 Navigate to Backend Directory

```bash
cd backend
```

### 1.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Set Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue
SECRET_KEY=dev-secret-key-change-in-production
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
WORKER_POOL_SIZE=3
WORKER_LEASE_TTL_SECONDS=300
WORKER_MAX_RETRIES=3
WORKER_POLL_INTERVAL_SECONDS=1
DEFAULT_RATE_LIMIT_PER_MINUTE=10
DEFAULT_MAX_CONCURRENT_JOBS=5
DEBUG=true
EOF
```

### 1.5 Run Database Migrations

Create all tables in your database:

```bash
alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial migration
```

### 1.6 Create a Test User

```bash
python scripts/create_user.py tenant1 my-api-key-123
```

You should see:
```
User created successfully!
  User ID: tenant1
  API Key: my-api-key-123
  Max Concurrent Jobs: 5
  Rate Limit: 10 per minute

Use this API key in the dashboard: my-api-key-123
```

## Step 2: Start Backend Services

### 2.1 Start API Server

Open a new terminal and run:

```bash
cd backend
source venv/bin/activate  # If not already activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2.2 Start Workers (Optional, in another terminal)

```bash
cd backend
source venv/bin/activate
python scripts/run_worker.py
```

You should see:
```
INFO:     worker_started worker_id=worker-1
INFO:     worker_started worker_id=worker-2
INFO:     worker_started worker_id=worker-3
```

## Step 3: Frontend Setup

### 3.1 Navigate to Frontend Directory

Open a new terminal:

```bash
cd frontend
```

### 3.2 Install Dependencies

```bash
npm install
```

### 3.3 Start Development Server

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

## Step 4: Test the Services

### 4.1 Test Backend API

#### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","message":"Service is running"}
```

#### API Documentation
Open in browser: http://localhost:8000/docs

#### Submit a Job (using curl)
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer my-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"task": "test", "data": {"message": "Hello World"}},
    "idempotency_key": "test-key-1",
    "max_retries": 3
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "tenant_id": "tenant1",
  "status": "pending",
  "payload": {"task": "test", "data": {"message": "Hello World"}},
  ...
}
```

#### Get Job Status
```bash
# Replace {job_id} with the ID from the previous response
curl http://localhost:8000/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer my-api-key-123"
```

#### Get Metrics
```bash
curl http://localhost:8000/api/v1/jobs/metrics/summary \
  -H "Authorization: Bearer my-api-key-123"
```

### 4.2 Test Frontend Dashboard

1. Open browser: http://localhost:3000
2. Enter API Key: `my-api-key-123`
3. Submit a test job:
   ```json
   {
     "task": "process_data",
     "data": {"id": 123, "name": "Test Job"}
   }
   ```
4. Watch the job status update in real-time!

## Step 5: Verify Everything Works

### Check Backend Logs

In the backend terminal, you should see:
- Job submission logs
- Worker processing logs (if workers are running)
- WebSocket connection logs

### Check Frontend Console

Open browser DevTools (F12) and check:
- No console errors
- WebSocket connection established
- API calls successful

### Test Job Processing

1. Submit a job via dashboard
2. Check backend logs - should see job being processed
3. Check dashboard - job status should change from "pending" → "running" → "completed"

## Troubleshooting

### Backend Issues

**"Module not found" error:**
```bash
# Make sure you're in backend directory and venv is activated
cd backend
source venv/bin/activate
```

**"Database connection failed":**
- Check your `.env` file has correct `DATABASE_URL`
- Verify database is accessible: `ping dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com`
- Check if SSL is required (add `?sslmode=require` to URL)

**"Table doesn't exist":**
```bash
# Run migrations again
alembic upgrade head
```

### Frontend Issues

**"Cannot connect to API":**
- Check backend is running on port 8000
- Check CORS settings in backend
- Verify `vite.config.js` proxy settings

**"WebSocket connection failed":**
- Check backend WebSocket endpoint: `ws://localhost:8000/ws`
- Check browser console for errors
- Verify backend is running

### Port Already in Use

**Port 8000 in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Port 3000 in use:**
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9

# Or change in vite.config.js
```

## Quick Test Script

Create a test script to verify everything:

```bash
# test_setup.sh
#!/bin/bash

echo "Testing Backend..."
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ Backend is running" || echo "❌ Backend not responding"

echo "Testing Frontend..."
curl -s http://localhost:3000 | grep -q "root" && echo "✅ Frontend is running" || echo "❌ Frontend not responding"

echo "Testing API with auth..."
curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer my-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"test": true}}' | grep -q "id" && echo "✅ API is working" || echo "❌ API test failed"
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Explore API docs at http://localhost:8000/docs

