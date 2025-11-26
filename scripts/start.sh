#!/bin/bash

# Start script for the job processor system

echo "🚀 Starting Distributed Task Queue & Job Processor..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if database exists (PostgreSQL)
echo "🗄️  Checking database connection..."
python -c "
import asyncio
from app.infrastructure.persistence.database import engine
from app.core.config import settings

async def check_db():
    try:
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        print(f'Please ensure PostgreSQL is running and DATABASE_URL is correct: {settings.DATABASE_URL}')
        exit(1)

asyncio.run(check_db())
"

# Create tables
echo "📊 Creating database tables..."
python -c "
import asyncio
from app.infrastructure.persistence.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tables created')

asyncio.run(create_tables())
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the system:"
echo "  1. Start API server:  uvicorn app.main:app --reload"
echo "  2. Start workers:     python scripts/run_worker.py"
echo "  3. Start frontend:    cd frontend && npm install && npm run dev"
echo ""
echo "Don't forget to create a user first:"
echo "  python scripts/create_user.py tenant1 my-api-key-123"

