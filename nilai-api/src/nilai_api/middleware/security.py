"""Security middleware for request size, timeout, and security headers.

This module provides middleware for:
- Request size limits (prevent large payload attacks)
- Request timeout limits (prevent long-running abuse)
- Security headers (HSTS, X-Content-Type-Options, etc.)
"""

import asyncio
import os
import time
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


# Configuration from environment variables
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))  # 10MB default
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # 60 seconds default


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit the size of incoming requests.

    Prevents large payload attacks by rejecting requests exceeding the maximum size.
    """

    def __init__(self, app, max_size: int = MAX_REQUEST_SIZE):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable):
        # Check Content-Length header first (fast path)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Maximum allowed size: {self.max_size} bytes",
            )

        # For streaming requests without Content-Length, check while reading
        # (handled by FastAPI's request body size limit)

        response = await call_next(request)
        return response


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request timeout limits.

    Prevents long-running requests from consuming resources indefinitely.
    """

    def __init__(self, app, timeout: int = REQUEST_TIMEOUT):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            # Use asyncio.timeout for clean timeout handling
            async with asyncio.timeout(self.timeout):
                response = await call_next(request)
                return response
        except TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request exceeded timeout limit of {self.timeout} seconds",
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Implements security best practices for HTTP headers:
    - HSTS (HTTP Strict Transport Security)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable):
        response: Response = await call_next(request)

        # HSTS: Enforce HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (API-only, no inline scripts)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'none'"

        # Permissions Policy (disable unnecessary features)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics.

    Adds timing information and request ID to logs.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id", str(time.time()))
        start_time = time.monotonic()

        # Add request ID to request state for logging
        request.state.request_id = request_id

        response = await call_next(request)

        # Calculate request duration
        duration = time.monotonic() - start_time

        # Add timing header
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


# Export all middleware
__all__ = [
    "RequestSizeLimitMiddleware",
    "RequestTimeoutMiddleware",
    "SecurityHeadersMiddleware",
    "RequestMetricsMiddleware",
    "MAX_REQUEST_SIZE",
    "REQUEST_TIMEOUT",
]
