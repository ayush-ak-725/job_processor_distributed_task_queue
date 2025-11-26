#!/bin/bash

# Local setup script for backend and frontend

set -e

echo "🚀 Setting up Local Development Environment"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Backend Setup
echo -e "${YELLOW}📦 Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
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
    echo -e "${GREEN}✅ Created .env file${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head || echo "⚠️  Migration may have failed - check database connection"

# Create test user if it doesn't exist
echo "Creating test user..."
python scripts/create_user.py tenant1 my-api-key-123 2>/dev/null || echo "⚠️  User may already exist"

cd ..

# Frontend Setup
echo ""
echo -e "${YELLOW}📦 Setting up Frontend...${NC}"
cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo -e "${GREEN}✅ Node modules already installed${NC}"
fi

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Start Backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Start Workers (Terminal 2, optional):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python scripts/run_worker.py"
echo ""
echo "3. Start Frontend (Terminal 3):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Access services:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "5. Test API Key: my-api-key-123"

