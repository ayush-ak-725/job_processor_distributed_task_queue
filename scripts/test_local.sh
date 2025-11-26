#!/bin/bash

# Quick test script for local setup

echo "🧪 Testing Local Setup..."
echo ""

# Test Backend Health
echo "1. Testing Backend Health..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend not responding (make sure it's running on port 8000)"
    echo "   Run: cd backend && uvicorn app.main:app --reload"
fi

# Test Frontend
echo "2. Testing Frontend..."
FRONTEND_RESPONSE=$(curl -s http://localhost:3000 2>/dev/null)
if echo "$FRONTEND_RESPONSE" | grep -q "root\|React"; then
    echo "   ✅ Frontend is running"
else
    echo "   ❌ Frontend not responding (make sure it's running on port 3000)"
    echo "   Run: cd frontend && npm run dev"
fi

# Test API with auth
echo "3. Testing API Authentication..."
API_TEST=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer my-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{"payload": {"test": true}}' 2>/dev/null)

if echo "$API_TEST" | grep -q "id"; then
    echo "   ✅ API is working"
    JOB_ID=$(echo "$API_TEST" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "   📝 Created job ID: $JOB_ID"
else
    echo "   ❌ API test failed"
    echo "   Response: $API_TEST"
    echo "   Make sure you created a user: python backend/scripts/create_user.py tenant1 my-api-key-123"
fi

echo ""
echo "✨ Test complete!"
echo ""
echo "Access services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"

