"""Script to create a test user"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.persistence.database import AsyncSessionLocal
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.core.domain.user import User
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(user_id: str, api_key: str, name: str = None):
    """Create a new user"""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        
        # Hash API key
        api_key_hash = api_key  # For prototype, store as-is. In production, use: pwd_context.hash(api_key)
        
        user = User(
            id=user_id,
            api_key_hash=api_key_hash,
            name=name or user_id,
            max_concurrent_jobs=settings.DEFAULT_MAX_CONCURRENT_JOBS,
            rate_limit_per_minute=settings.DEFAULT_RATE_LIMIT_PER_MINUTE,
        )
        
        created_user = await user_repo.create(user)
        await session.commit()
        
        print(f"User created successfully!")
        print(f"  User ID: {created_user.id}")
        print(f"  API Key: {api_key}")
        print(f"  Max Concurrent Jobs: {created_user.max_concurrent_jobs}")
        print(f"  Rate Limit: {created_user.rate_limit_per_minute} per minute")
        print(f"\nUse this API key in the dashboard: {api_key}")


async def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_user.py <user_id> <api_key> [name]")
        print("Example: python scripts/create_user.py tenant1 my-api-key-123")
        sys.exit(1)
    
    user_id = sys.argv[1]
    api_key = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    
    await create_user(user_id, api_key, name)


if __name__ == "__main__":
    asyncio.run(main())

