# 📋 Distributed Task Queue & Job Processor

A small-scale **distributed job queue and worker system** built with Python (FastAPI) and PostgreSQL. It enables authenticated users to submit tasks, process them with worker nodes, and track progress in real-time through a web dashboard.

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐
│   Web Dashboard │ (React - Port 3000)
│   (WebSocket)   │
└────────┬────────┘
         │ HTTP/WebSocket
┌────────▼─────────────────────────────────────┐
│         FastAPI HTTP API (Port 8000)          │
│  ┌────────────────────────────────────────┐  │
│  │  Authentication & Rate Limiting        │  │
│  │  Job Service Layer                     │  │
│  └────────────────────────────────────────┘  │
└────────┬─────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────┐
│   PostgreSQL Database                          │
│  ┌────────────────────────────────────────┐  │
│  │  Jobs Table (Queue)                     │  │
│  │  Users Table                           │  │
│  │  DLQ Table                             │  │
│  │  Metrics Table                         │  │
│  └────────────────────────────────────────┘  │
└────────┬─────────────────────────────────────┘
         │ SELECT FOR UPDATE SKIP LOCKED
┌────────▼─────────────────────────────────────┐
│      Worker Pool (Multiple Processes)          │
│  - Lease Management                           │
│  - Retry Logic                               │
│  - Dead Letter Queue                         │
└───────────────────────────────────────────────┘
```

### Service Architecture (Docker)

The application is split into **separate services** that can be deployed independently:

- **Backend Service**: FastAPI application (API + Business Logic)
- **Worker Service**: Job processing workers (can scale horizontally)
- **Frontend Service**: React dashboard (Nginx-served)
- **PostgreSQL Service**: Database

Each service has its own Dockerfile and can be built/deployed separately.

## 🐳 Docker Deployment

### Quick Start with Docker

1. **Clone the repository:**
```bash
git clone <repository-url>
cd job_processor_distributed_task_queue
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services (Development):**
```bash
# Using docker-compose
docker-compose -f docker-compose.dev.yml up -d

# Or using Makefile
make up
```

4. **Start all services (Production):**
```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or using Makefile
make up-prod
```

5. **Create a test user:**
```bash
# Using docker-compose
docker-compose exec backend python scripts/create_user.py tenant1 my-api-key-123

# Or using Makefile
make create-user USER_ID=tenant1 API_KEY=my-api-key-123
```

6. **Access the services:**
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Docker Services

#### Backend Service
- **Dockerfile**: `backend/Dockerfile`
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Build**: `docker build -f backend/Dockerfile -t job-queue-backend .`

#### Worker Service
- **Dockerfile**: `backend/Dockerfile.worker`
- **Scales**: Horizontally (multiple replicas)
- **Build**: `docker build -f backend/Dockerfile.worker -t job-queue-worker .`

#### Frontend Service
- **Dockerfile**: `frontend/Dockerfile` (production)
- **Dockerfile.dev**: `frontend/Dockerfile.dev` (development)
- **Port**: 3000 (dev) / 80 (prod)
- **Build**: `docker build -f frontend/Dockerfile -t job-queue-frontend ./frontend`

### Docker Compose Files

#### Development (`docker-compose.dev.yml`)
- Hot reload enabled
- Volume mounts for live code updates
- Development-friendly configuration

#### Production (`docker-compose.prod.yml`)
- Optimized builds
- Resource limits
- Logging configuration
- Health checks
- Horizontal scaling support

### Makefile Commands

```bash
make help              # Show all available commands
make build             # Build all Docker images
make up                # Start development environment
make up-prod           # Start production environment
make down              # Stop all services
make logs              # View all logs
make logs-backend      # View backend logs
make logs-worker       # View worker logs
make logs-frontend     # View frontend logs
make test              # Run tests
make create-user       # Create a test user
make scale-workers     # Scale workers (COUNT=3)
make clean             # Remove all containers and volumes
```

### Building Individual Services

#### Backend
```bash
cd backend
docker build -f Dockerfile -t job-queue-backend:latest .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/job_queue_db \
  job-queue-backend:latest
```

#### Frontend
```bash
cd frontend
docker build -f Dockerfile -t job-queue-frontend:latest .
docker run -p 3000:80 job-queue-frontend:latest
```

#### Worker
```bash
cd backend
docker build -f Dockerfile.worker -t job-queue-worker:latest .
docker run \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/job_queue_db \
  job-queue-worker:latest
```

### Scaling Workers

Scale workers horizontally:
```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d --scale worker=5

# Or using Makefile
make scale-workers COUNT=5
```

## 📦 Manual Installation (Without Docker)

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Node.js 18+ (for frontend)

### Backend Setup

1. **Navigate to backend:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database:**
```bash
createdb job_queue_db
```

5. **Configure environment:**
```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/job_queue_db
```

6. **Create a test user:**
```bash
python scripts/create_user.py tenant1 my-api-key-123
```

7. **Start the API server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Start workers (in a separate terminal):**
```bash
python scripts/run_worker.py
```

### Frontend Setup

1. **Navigate to frontend:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm run dev
```

4. **Build for production:**
```bash
npm run build
```

## 📖 Usage

### API Endpoints

#### Submit a Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer my-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"task": "process_data", "data": {"id": 123}},
    "idempotency_key": "unique-key-123",
    "max_retries": 3
  }'
```

#### Get Job Status
```bash
curl http://localhost:8000/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer my-api-key-123"
```

#### List Jobs
```bash
curl http://localhost:8000/api/v1/jobs?status=pending \
  -H "Authorization: Bearer my-api-key-123"
```

#### Get Metrics
```bash
curl http://localhost:8000/api/v1/jobs/metrics/summary \
  -H "Authorization: Bearer my-api-key-123"
```

#### Get DLQ Jobs
```bash
curl http://localhost:8000/api/v1/jobs/dlq \
  -H "Authorization: Bearer my-api-key-123"
```

### Dashboard Usage

1. **Enter API Key**: Use the API key created with `create_user.py`
2. **Submit Jobs**: Use the form to submit new jobs
3. **Monitor**: View real-time job status, metrics, and DLQ items
4. **Filter**: Filter jobs by status (Pending, Running, Completed, Failed, DLQ)

## 🧪 Testing

Run tests:
```bash
# With Docker
docker-compose exec backend pytest tests/ -v

# Or manually
cd backend
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📊 Observability

### Logging
Structured logging with trace IDs:
```python
logger.info(
    "job_submitted",
    job_id=str(job.id),
    tenant_id=job.tenant_id,
    trace_id=job.trace_id,
)
```

### Metrics
Access metrics via API:
```bash
GET /api/v1/jobs/metrics/summary
```

Returns:
```json
{
  "total_jobs": 100,
  "pending_jobs": 5,
  "running_jobs": 3,
  "completed_jobs": 90,
  "failed_jobs": 1,
  "dlq_jobs": 1
}
```

### Events
Events are published via the event bus and broadcast to WebSocket clients:
- `job_submitted`
- `job_started`
- `job_completed`
- `job_failed`
- `job_retry`
- `job_dlq`

## 🔒 Security

- **Authentication**: API key-based (Bearer token)
- **Rate Limiting**: Token bucket algorithm per tenant
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM

## 🔄 Job Processing Flow

1. **Submit**: Client submits job via API
2. **Enqueue**: Job stored in database with `PENDING` status
3. **Dequeue**: Worker polls using `SELECT FOR UPDATE SKIP LOCKED`
4. **Lease**: Worker acquires lease (atomic update with TTL)
5. **Process**: Worker executes job logic
6. **Ack**: On success, mark as `COMPLETED`; on failure, mark as `FAILED`
7. **Retry**: If failed and retries available, increment retry count and reset to `PENDING`
8. **DLQ**: If max retries exceeded, move to Dead Letter Queue

## 📝 Project Structure

```
job_processor_distributed_task_queue/
├── backend/              # Backend service
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   ├── scripts/         # Utility scripts
│   ├── Dockerfile       # Backend Docker image
│   ├── Dockerfile.worker # Worker Docker image
│   └── requirements.txt # Python dependencies
├── frontend/            # Frontend service
│   ├── src/            # React source code
│   ├── Dockerfile      # Production Docker image
│   ├── Dockerfile.dev  # Development Docker image
│   ├── nginx.conf      # Nginx configuration
│   └── package.json    # Node dependencies
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
├── docker-compose.prod.yml # Production compose (optimized)
├── Makefile            # Convenience commands
└── README.md          # This file
```

## 🚀 Deployment

### Production Deployment

1. **Build production images:**
```bash
make build-prod
```

2. **Set environment variables:**
```bash
export POSTGRES_PASSWORD=secure-password
export SECRET_KEY=your-secret-key
export WORKER_REPLICAS=3
```

3. **Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Scale workers:**
```bash
docker-compose -f docker-compose.prod.yml up -d --scale worker=5
```

### Kubernetes Deployment (Future)

Each service can be deployed as separate Kubernetes deployments:
- `backend-deployment.yaml`
- `worker-deployment.yaml`
- `frontend-deployment.yaml`
- `postgres-statefulset.yaml`

## 🎯 Design Trade-offs

### PostgreSQL as Queue
**Pros:**
- Single database for all data
- ACID guarantees
- Durable and reliable
- No additional infrastructure

**Cons:**
- Lower throughput than dedicated message brokers (Redis, RabbitMQ)
- Database becomes a bottleneck at very high scale

**When to Consider Alternatives:**
- > 10,000 jobs/second throughput
- Need pub/sub features
- Want message TTL/expiration

### Lease-Based Processing
**Pros:**
- Prevents duplicate processing
- Automatic recovery of stale leases
- Fault-tolerant

**Cons:**
- Requires lease TTL tuning
- Slight delay in job recovery

### Rate Limiting (In-Memory)
**Pros:**
- Fast and simple
- No database overhead

**Cons:**
- Not distributed (per-process)
- Lost on restart

**For Production:** Use Redis-based rate limiting for distributed systems

## 🐛 Troubleshooting

### Docker Issues

**Containers not starting:**
```bash
docker-compose logs
docker-compose ps
```

**Database connection issues:**
```bash
docker-compose exec postgres pg_isready -U postgres
docker-compose exec backend python -c "from app.infrastructure.persistence.database import engine; import asyncio; asyncio.run(engine.connect())"
```

**Build failures:**
```bash
docker-compose build --no-cache
```

### Database Connection Issues
- Check PostgreSQL is running: `docker-compose ps postgres`
- Verify `DATABASE_URL` in environment
- Check database exists: `docker-compose exec postgres psql -l`

### Workers Not Processing Jobs
- Check worker logs: `docker-compose logs worker`
- Verify database connection
- Check lease TTL settings
- Ensure jobs are in `PENDING` status

### WebSocket Not Connecting
- Check CORS settings
- Verify WebSocket endpoint: `ws://localhost:8000/ws`
- Check browser console for errors
- Verify nginx configuration (production)

## 📄 License

This project is a prototype demonstration. Use at your own risk.

## 👥 Contributing

This is a prototype project. For production use, consider:
- Adding comprehensive test coverage
- Implementing proper API key hashing
- Adding database migrations workflow
- Setting up CI/CD
- Adding monitoring/alerting
- Implementing distributed rate limiting

---

**Built with ❤️ following SOLID principles and design patterns**
