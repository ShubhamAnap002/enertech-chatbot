from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter suitable for single-process deployments."""

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path.split('/')[1:3]}"
        now = time.time()
        bucket = [t for t in self._hits.get(key, []) if now - t < self.window_seconds]
        if len(bucket) >= self.max_requests:
            return Response("Rate limit exceeded", status_code=429)
        bucket.append(now)
        self._hits[key] = bucket
        return await call_next(request)
