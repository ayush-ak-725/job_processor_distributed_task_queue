"""Rate limiting middleware"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.services.rate_limiter import rate_limiter
from app.core.exceptions.custom_exceptions import RateLimitExceededError


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in ["/docs", "/openapi.json", "/metrics", "/health"]:
            return await call_next(request)
        
        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user:
            try:
                rate_limiter.check_rate_limit(
                    user.id, user.rate_limit_per_minute
                )
            except RateLimitExceededError as e:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=str(e),
                )
        
        response = await call_next(request)
        return response

