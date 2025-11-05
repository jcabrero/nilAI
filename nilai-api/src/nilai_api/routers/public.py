# Fast API and serving
import time

from fastapi import APIRouter, HTTPException, status

from nilai_api.state import state

# Internal libraries
from nilai_common import HealthCheckResponse


router = APIRouter()

# Track application start time for uptime
_start_time = time.monotonic()


@router.get("/v1/public_key", tags=["Public"])
async def get_public_key() -> str:
    """
    Get the public key of the API.
    """
    return state.b64_public_key


# Health Check Endpoint
@router.get("/v1/health", tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    Perform a system health check.

    - **Returns**: Current system health status and uptime

    ### Health Check Details
    - Provides a quick verification of system operational status
    - Reports current system uptime

    ### Status Indicators
    - `status`: Indicates system operational condition
      - `"ok"`: System is functioning normally
    - `uptime`: Duration the system has been running

    ### Example
    ```python
    # Retrieve system health status
    health = await health_check()
    # Expect: HealthCheckResponse(status='ok', uptime=3600)
    ```
    """
    return HealthCheckResponse(status="ok", uptime=state.uptime)


@router.get("/healthz", tags=["Health"])
async def healthz() -> dict[str, str]:
    """
    Kubernetes liveness probe endpoint.

    Fast health check that verifies the application is running.
    Returns immediately without checking dependencies.

    - **Returns**: Simple status indicating the application is alive

    ### Use Case
    - Kubernetes liveness probes
    - Load balancer health checks
    - Quick service verification

    ### Response
    - `200 OK`: Application is running
    - Response time: < 10ms (no I/O operations)

    ### Example
    ```bash
    curl http://localhost:8080/healthz
    # {"status": "healthy", "uptime": "123.45s"}
    ```
    """
    uptime_seconds = time.monotonic() - _start_time
    return {"status": "healthy", "uptime": f"{uptime_seconds:.2f}s"}


@router.get("/readyz", tags=["Health"])
async def readyz() -> dict[str, str | dict]:
    """
    Kubernetes readiness probe endpoint.

    Comprehensive readiness check that verifies the application can handle traffic.
    Checks critical dependencies like model availability.

    - **Returns**: Status with dependency checks
    - **503 Service Unavailable**: If critical dependencies are not ready

    ### Checks Performed
    1. Application is running
    2. Models are registered and available
    3. State management is functional

    ### Use Case
    - Kubernetes readiness probes
    - Load balancer traffic routing decisions
    - Pre-deployment verification

    ### Response Codes
    - `200 OK`: Service is ready to handle requests
    - `503 Service Unavailable`: Service is not ready (dependencies unavailable)

    ### Example
    ```bash
    # Service ready
    curl http://localhost:8080/readyz
    # {"status": "ready", "checks": {"models": "ok", "state": "ok"}}

    # Service not ready
    curl http://localhost:8080/readyz
    # HTTP 503 {"status": "not_ready", "reason": "no models available"}
    ```
    """
    checks: dict[str, str] = {}

    # Check if models are available
    try:
        models = state.get_models()
        if not models:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "reason": "no models available",
                    "checks": {"models": "unavailable", "state": "ok"},
                },
            )
        checks["models"] = "ok"
        checks["model_count"] = str(len(models))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": f"model check failed: {e}",
                "checks": {"models": "error", "state": "unknown"},
            },
        )

    # Check state management
    try:
        # Simple check that state is accessible
        _ = state.uptime
        checks["state"] = "ok"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": f"state check failed: {e}",
                "checks": {**checks, "state": "error"},
            },
        )

    return {"status": "ready", "checks": checks}
