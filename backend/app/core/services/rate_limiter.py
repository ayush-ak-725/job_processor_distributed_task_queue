"""Rate limiter service using token bucket algorithm"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

from app.core.exceptions.custom_exceptions import RateLimitExceededError


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = datetime.utcnow()
    
    def refill(self) -> None:
        """Refill tokens based on time elapsed"""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """Rate limiter service using token bucket algorithm"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
    
    def _get_bucket_key(self, tenant_id: str) -> str:
        """Get bucket key for tenant"""
        return f"rate_limit:{tenant_id}"
    
    def _get_or_create_bucket(
        self, tenant_id: str, rate_per_minute: int
    ) -> TokenBucket:
        """Get or create token bucket for tenant"""
        key = self._get_bucket_key(tenant_id)
        if key not in self.buckets:
            # Convert rate per minute to tokens per second
            refill_rate = rate_per_minute / 60.0
            self.buckets[key] = TokenBucket(
                capacity=rate_per_minute, refill_rate=refill_rate
            )
        return self.buckets[key]
    
    def check_rate_limit(self, tenant_id: str, rate_per_minute: int) -> None:
        """Check if request is within rate limit"""
        bucket = self._get_or_create_bucket(tenant_id, rate_per_minute)
        
        if not bucket.consume():
            raise RateLimitExceededError(
                f"Rate limit exceeded. Limit: {rate_per_minute} requests per minute"
            )
    
    def reset_bucket(self, tenant_id: str) -> None:
        """Reset bucket for tenant (useful for testing)"""
        key = self._get_bucket_key(tenant_id)
        if key in self.buckets:
            del self.buckets[key]


# Global rate limiter instance
rate_limiter = RateLimiter()

