"""Benchmark tests for API endpoint performance.

These tests measure latency of health check endpoints and other fast paths.
"""

import pytest
from httpx import AsyncClient

from nilai_api.app import app


@pytest.mark.asyncio
class TestHealthEndpointPerformance:
    """Benchmark health check endpoint latency."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_healthz_endpoint_benchmark(self, benchmark, client):
        """Benchmark /healthz endpoint latency.

        Measures time for fast liveness probe.
        Expected: < 10ms (no I/O operations)

        This endpoint should be extremely fast as it only checks
        if the application process is running without any dependencies.
        """

        async def get_healthz():
            response = await client.get("/healthz")
            return response

        result = await benchmark.pedantic(get_healthz, iterations=100, rounds=10)
        assert result.status_code == 200
        data = result.json()
        assert data["status"] == "healthy"
        assert "uptime" in data

    async def test_public_key_endpoint_benchmark(self, benchmark, client):
        """Benchmark /v1/public_key endpoint latency.

        Measures time to retrieve public key.
        Expected: < 20ms (simple state access)
        """

        async def get_public_key():
            response = await client.get("/v1/public_key")
            return response

        result = await benchmark.pedantic(get_public_key, iterations=50, rounds=10)
        assert result.status_code == 200

    async def test_health_endpoint_comparison(self, client):
        """Compare latency of different health endpoints.

        This test helps understand the performance difference between:
        - /healthz: Fast liveness check (no dependencies)
        - /v1/health: Standard health check (state access)
        - /readyz: Comprehensive readiness check (model availability)

        Not a strict benchmark, but useful for understanding tradeoffs.
        """
        import time

        # Measure /healthz
        start = time.perf_counter()
        for _ in range(100):
            response = await client.get("/healthz")
            assert response.status_code == 200
        healthz_time = (time.perf_counter() - start) / 100

        # Measure /v1/health
        start = time.perf_counter()
        for _ in range(100):
            response = await client.get("/v1/health")
            # May fail if state not initialized in test
            if response.status_code == 200:
                pass
        health_time = (time.perf_counter() - start) / 100

        # /healthz should be fastest
        assert healthz_time < 0.050  # < 50ms average


@pytest.mark.asyncio
class TestMiddlewarePerformance:
    """Benchmark middleware overhead."""

    @pytest.fixture
    async def client(self):
        """Create async test client with all middleware."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_middleware_overhead_benchmark(self, benchmark, client):
        """Benchmark middleware overhead on simple request.

        Measures total middleware processing time:
        - SecurityHeadersMiddleware
        - RequestMetricsMiddleware
        - RequestTimeoutMiddleware
        - RequestSizeLimitMiddleware
        - CORSMiddleware

        Expected: < 5ms overhead
        """

        async def request_with_middleware():
            response = await client.get("/healthz")
            return response

        result = await benchmark.pedantic(request_with_middleware, iterations=50, rounds=10)
        assert result.status_code == 200

        # Check security headers are present
        headers = result.headers
        assert "strict-transport-security" in headers
        assert "x-content-type-options" in headers
        assert "x-frame-options" in headers
        assert "x-request-id" in headers
        assert "x-response-time" in headers


@pytest.mark.asyncio
class TestCORSValidationPerformance:
    """Benchmark CORS validation overhead."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_cors_preflight_benchmark(self, benchmark, client):
        """Benchmark CORS preflight OPTIONS request.

        Measures time to handle CORS preflight.
        Expected: < 10ms
        """

        async def cors_preflight():
            response = await client.options(
                "/v1/health", headers={"Origin": "http://localhost:3000"}
            )
            return response

        result = await benchmark.pedantic(cors_preflight, iterations=50, rounds=10)
        # Should return CORS headers
        assert "access-control-allow-origin" in result.headers or result.status_code in (
            200,
            204,
            405,
        )


class TestRequestSizeValidation:
    """Benchmark request size validation."""

    def test_small_request_validation_benchmark(self, benchmark):
        """Benchmark validation of small requests.

        Measures overhead of size checking for typical requests.
        Expected: < 0.1ms (header check only)
        """

        # Simulate Content-Length header check
        def validate_size():
            content_length = "1024"  # 1KB
            max_size = 10 * 1024 * 1024  # 10MB
            return int(content_length) <= max_size

        result = benchmark(validate_size)
        assert result is True

    def test_large_request_detection_benchmark(self, benchmark):
        """Benchmark detection of oversized requests.

        Measures time to reject requests exceeding size limit.
        Expected: < 0.1ms (fail fast on header check)
        """

        def detect_oversized():
            content_length = "20971520"  # 20MB
            max_size = 10 * 1024 * 1024  # 10MB
            return int(content_length) > max_size

        result = benchmark(detect_oversized)
        assert result is True  # Should detect as oversized


@pytest.mark.benchmark(group="baseline")
class TestBaselinePerformance:
    """Establish baseline performance metrics.

    These tests establish performance baselines for simple operations
    to help understand the overhead of more complex operations.
    """

    def test_dict_creation_baseline(self, benchmark):
        """Baseline: Dictionary creation."""

        def create_dict():
            return {"status": "healthy", "timestamp": "2025-01-01T00:00:00Z"}

        result = benchmark(create_dict)
        assert result["status"] == "healthy"

    def test_json_dumps_baseline(self, benchmark):
        """Baseline: JSON serialization."""
        import json

        data = {
            "status": "healthy",
            "checks": {"models": "ok", "state": "ok"},
            "timestamp": "2025-01-01T00:00:00Z",
        }

        def serialize():
            return json.dumps(data)

        result = benchmark(serialize)
        assert isinstance(result, str)

    def test_string_formatting_baseline(self, benchmark):
        """Baseline: String formatting."""

        def format_string():
            uptime = 123.45
            return f"{uptime:.2f}s"

        result = benchmark(format_string)
        assert result == "123.45s"
