"""User/Tenant domain entity"""

from typing import Optional


class User:
    """User/Tenant domain entity"""
    
    def __init__(
        self,
        id: str,
        api_key_hash: str,
        max_concurrent_jobs: int = 5,
        rate_limit_per_minute: int = 10,
        name: Optional[str] = None,
    ):
        self.id = id
        self.api_key_hash = api_key_hash
        self.max_concurrent_jobs = max_concurrent_jobs
        self.rate_limit_per_minute = rate_limit_per_minute
        self.name = name
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, name={self.name})"

