# 🚀 Deployment Guide

This guide covers deploying the Distributed Task Queue & Job Processor as separate Docker services.

## 📦 Service Architecture

The application consists of **4 independent services**:

1. **Backend Service** (`backend/`)
   - FastAPI application
   - REST API endpoints
   - WebSocket server
   - Dockerfile: `backend/Dockerfile`

2. **Worker Service** (`backend/`)
   - Job processing workers
   - Horizontally scalable
   - Dockerfile: `backend/Dockerfile.worker`

3. **Frontend Service** (`frontend/`)
   - React dashboard
   - Nginx-served static files
   - Dockerfile: `frontend/Dockerfile`

4. **PostgreSQL Service**
   - Database
   - Persistent storage

## 🐳 Building Individual Services

### Backend Service

```bash
# Build backend image
docker build -f backend/Dockerfile -t job-queue-backend:latest .

# Run backend (requires external database)
docker run -d \
  --name job-queue-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  job-queue-backend:latest
```

### Worker Service

```bash
# Build worker image
docker build -f backend/Dockerfile.worker -t job-queue-worker:latest .

# Run worker (requires external database)
docker run -d \
  --name job-queue-worker \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e WORKER_POOL_SIZE=5 \
  job-queue-worker:latest

# Scale workers
docker run -d --name job-queue-worker-1 job-queue-worker:latest
docker run -d --name job-queue-worker-2 job-queue-worker:latest
docker run -d --name job-queue-worker-3 job-queue-worker:latest
```

### Frontend Service

```bash
# Build frontend image
docker build -f frontend/Dockerfile -t job-queue-frontend:latest ./frontend

# Run frontend (requires backend API)
docker run -d \
  --name job-queue-frontend \
  -p 3000:80 \
  job-queue-frontend:latest
```

## 🎯 Deployment Scenarios

### Scenario 1: All Services Together (Docker Compose)

**Best for**: Development, small deployments, single server

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 2: Separate Services on Different Servers

**Best for**: Production, high availability, scaling

#### Server 1: Database
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=secure-password \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine
```

#### Server 2: Backend API
```bash
docker run -d \
  --name backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@server1:5432/db \
  job-queue-backend:latest
```

#### Server 3: Workers (Multiple)
```bash
# Worker 1
docker run -d \
  --name worker-1 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@server1:5432/db \
  job-queue-worker:latest

# Worker 2
docker run -d \
  --name worker-2 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@server1:5432/db \
  job-queue-worker:latest
```

#### Server 4: Frontend
```bash
docker run -d \
  --name frontend \
  -p 3000:80 \
  job-queue-frontend:latest
```

### Scenario 3: Kubernetes Deployment

Each service can be deployed as separate Kubernetes deployments.

#### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-queue-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: job-queue-backend
  template:
    metadata:
      labels:
        app: job-queue-backend
    spec:
      containers:
      - name: backend
        image: job-queue-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

#### Worker Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-queue-worker
spec:
  replicas: 5  # Scale workers independently
  selector:
    matchLabels:
      app: job-queue-worker
  template:
    metadata:
      labels:
        app: job-queue-worker
    spec:
      containers:
      - name: worker
        image: job-queue-worker:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 🔧 Configuration

### Environment Variables

#### Backend Service
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secret-key
API_HOST=0.0.0.0
API_PORT=8000
WORKER_POOL_SIZE=5
DEFAULT_RATE_LIMIT_PER_MINUTE=10
DEFAULT_MAX_CONCURRENT_JOBS=5
```

#### Worker Service
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
WORKER_POOL_SIZE=5
WORKER_LEASE_TTL_SECONDS=300
WORKER_MAX_RETRIES=3
WORKER_POLL_INTERVAL_SECONDS=1
```

#### Frontend Service
```bash
# Build-time variables (for Vite)
VITE_API_URL=http://backend:8000
VITE_WS_URL=ws://backend:8000
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **Backend**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:3000/` (Nginx serves index.html)

### Docker Health Checks

All services include health checks:
```bash
# Check service health
docker ps  # Shows health status

# View health check logs
docker inspect <container-name> | grep -A 10 Health
```

## 🔄 Scaling

### Horizontal Scaling

#### Scale Workers
```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d --scale worker=10

# Using individual containers
for i in {1..10}; do
  docker run -d --name worker-$i job-queue-worker:latest
done
```

#### Scale Backend API
```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Add load balancer (nginx/traefik) in front
```

### Vertical Scaling

Adjust resource limits in `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

## 🔒 Security Best Practices

1. **Use Secrets Management**
   ```bash
   # Docker secrets
   echo "my-secret-key" | docker secret create secret_key -
   
   # Kubernetes secrets
   kubectl create secret generic db-secret \
     --from-literal=url=postgresql://...
   ```

2. **Network Isolation**
   ```yaml
   networks:
     backend_network:
       internal: true  # No external access
   ```

3. **Non-root User**
   - All Dockerfiles use non-root user (`appuser`)

4. **Image Scanning**
   ```bash
   docker scan job-queue-backend:latest
   ```

## 📝 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build backend
        run: docker build -f backend/Dockerfile -t job-queue-backend:${{ github.sha }} .
      - name: Push to registry
        run: docker push job-queue-backend:${{ github.sha }}

  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build frontend
        run: docker build -f frontend/Dockerfile -t job-queue-frontend:${{ github.sha }} ./frontend
      - name: Push to registry
        run: docker push job-queue-frontend:${{ github.sha }}
```

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker logs <container-name>

# Check environment variables
docker exec <container-name> env

# Check network connectivity
docker exec <container-name> ping postgres
```

### Database Connection Issues
```bash
# Test connection from backend
docker exec job-queue-backend python -c "
from app.infrastructure.persistence.database import engine
import asyncio
asyncio.run(engine.connect())
"
```

### Workers Not Processing
```bash
# Check worker logs
docker logs job-queue-worker

# Check database for pending jobs
docker exec postgres psql -U postgres -d job_queue_db -c "SELECT COUNT(*) FROM jobs WHERE status='pending';"
```

---

For more information, see the main [README.md](README.md).

