# 🚀 Starting Services Locally

## ✅ Setup Complete!

- ✅ Python 3.11 virtual environment created
- ✅ All dependencies installed
- ✅ Database migrations run successfully
- ✅ Test user created

## Start Services

### Terminal 1: Backend API Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2: Workers (Optional - for processing jobs)

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

### Terminal 3: Frontend Dashboard

```bash
cd frontend
npm install  # If not already done
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

## Access Services

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Test API Key

Use this API key in the dashboard:
```
my-api-key-123
```

## Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Submit a test job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer my-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"task": "test", "data": {"message": "Hello World"}},
    "idempotency_key": "test-1"
  }'
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database Connection Issues
- Check your `.env` file has correct `DATABASE_URL`
- Verify database is accessible

### Module Not Found
- Make sure virtual environment is activated: `source venv/bin/activate`
- Make sure you're in the `backend/` directory

## Next Steps

1. Open http://localhost:3000 in your browser
2. Enter API key: `my-api-key-123`
3. Submit a test job
4. Watch it process in real-time!

