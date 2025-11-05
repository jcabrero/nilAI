# Code Style Guide

**NilAI Python Code Style & Best Practices**

This document defines the coding standards and best practices for the NilAI project. Following these guidelines ensures consistency, maintainability, and quality across the codebase.

---

## Table of Contents

1. [Python Version & General Principles](#python-version--general-principles)
2. [Code Formatting](#code-formatting)
3. [Type Annotations](#type-annotations)
4. [Async Programming](#async-programming)
5. [FastAPI Patterns](#fastapi-patterns)
6. [Pydantic Models & DTOs](#pydantic-models--dtos)
7. [Error Handling](#error-handling)
8. [Logging](#logging)
9. [Testing](#testing)
10. [Module Organization](#module-organization)
11. [Documentation](#documentation)
12. [Security](#security)

---

## Python Version & General Principles

### Python Version
- **Target:** Python 3.12+
- Use modern Python features (pattern matching, improved type hints, etc.)

### Core Principles
1. **Explicit is better than implicit** - Clear, readable code over clever tricks
2. **Async-first** - All I/O should be async (database, HTTP, file operations)
3. **Type safety** - Comprehensive type annotations enforced by pyright
4. **Fail fast** - Validate early; use Pydantic models for all external data
5. **Separation of concerns** - Clear boundaries between API, business logic, and infrastructure

---

## Code Formatting

### Tools
- **Formatter:** `ruff format` (automatically applied by pre-commit)
- **Linter:** `ruff check` (comprehensive rule set)

### Style Rules
- **Line length:** 100 characters (enforced by ruff)
- **Quotes:** Double quotes for strings (`"hello"`, not `'hello'`)
- **Indentation:** 4 spaces (no tabs)
- **Imports:** Sorted and grouped by ruff (isort integration)

### Import Organization
```python
# Standard library imports
import asyncio
import logging
from typing import Annotated

# Third-party imports
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

# Local application imports
from nilai_api.auth import get_auth_info
from nilai_common.types import ChatRequest
```

**Import Rules:**
- Group imports: stdlib → third-party → local
- Use absolute imports for local packages
- Avoid wildcard imports (`from module import *`)
- Use `TYPE_CHECKING` for type-only imports to avoid circular dependencies

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nilai_api.models import User
```

---

## Type Annotations

### Type Annotation Requirements
- **All public functions** must have type annotations for parameters and return values
- **Class attributes** should be annotated
- **Use `None` explicitly** instead of omitting return type

### Examples

#### ✅ Good
```python
from typing import Optional

async def get_user(user_id: str) -> Optional[User]:
    """Fetch a user by ID."""
    result = await db.execute(query)
    return result

def calculate_total(prices: list[float], tax_rate: float = 0.1) -> float:
    """Calculate total with tax."""
    return sum(prices) * (1 + tax_rate)
```

#### ❌ Bad
```python
async def get_user(user_id):  # Missing type annotations
    result = await db.execute(query)
    return result

def calculate_total(prices, tax_rate=0.1):  # Missing type annotations
    return sum(prices) * (1 + tax_rate)
```

### Modern Type Hints (Python 3.12+)
```python
# Use built-in types instead of typing module when possible
def process_items(items: list[str]) -> dict[str, int]:  # ✅ Good
    return {item: len(item) for item in items}

def process_items(items: List[str]) -> Dict[str, int]:  # ❌ Outdated
    return {item: len(item) for item in items}
```

### FastAPI Dependency Types with Annotated
```python
from typing import Annotated
from fastapi import Depends

async def get_current_user() -> User:
    ...

UserDep = Annotated[User, Depends(get_current_user)]

@router.get("/profile")
async def get_profile(user: UserDep) -> ProfileResponse:
    return ProfileResponse(user=user)
```

---

## Async Programming

### Async Best Practices

#### 1. **All I/O must be async**
```python
# ✅ Good - Async I/O
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ Bad - Blocking I/O in async function
async def fetch_data(url: str) -> dict:
    response = requests.get(url)  # BLOCKS THE EVENT LOOP!
    return response.json()
```

#### 2. **Use `anyio.to_thread.run_sync` for unavoidable blocking calls**
```python
import anyio

async def process_large_file(file_path: str) -> bytes:
    """Process a large file without blocking the event loop."""
    def _read_file() -> bytes:
        with open(file_path, "rb") as f:
            return f.read()

    return await anyio.to_thread.run_sync(_read_file)
```

#### 3. **Context Managers**
Always use async context managers for resources:
```python
# ✅ Good
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# ✅ Good
async with asyncio.timeout(30):
    result = await slow_operation()
```

#### 4. **Concurrent Operations**
Use `asyncio.gather` for concurrent tasks:
```python
async def fetch_multiple_users(user_ids: list[str]) -> list[User]:
    tasks = [get_user(user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)
```

#### 5. **Avoid Async Antipatterns**
```python
# ❌ Bad - Sequential when it could be concurrent
async def bad_example():
    result1 = await operation1()
    result2 = await operation2()  # Waits for operation1
    return result1, result2

# ✅ Good - Concurrent
async def good_example():
    result1, result2 = await asyncio.gather(operation1(), operation2())
    return result1, result2
```

---

## FastAPI Patterns

### Dependency Injection
Use FastAPI's dependency injection system for all shared resources:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]

@router.get("/users/{user_id}")
async def get_user(user_id: str, db: DbSession) -> UserResponse:
    return await fetch_user(db, user_id)
```

### Lifespan Context
Use lifespan context for startup/shutdown logic:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = await setup_redis()
    db_engine = await setup_database()

    yield {"redis": redis_client, "db": db_engine}

    # Shutdown
    await redis_client.close()
    await db_engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### Response Models
Always define response models:

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    user_id: str
    email: str
    created_at: datetime

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    ...
```

### Background Tasks
Use `BackgroundTasks` for non-blocking operations:

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str) -> None:
    # This runs after the response is sent
    ...

@router.post("/send-notification")
async def notify(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Hello!")
    return {"status": "queued"}
```

---

## Pydantic Models & DTOs

### Model Definition
Use Pydantic v2 with `Field` for validation:

```python
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    model: str = Field(..., min_length=1, description="Model identifier")
    messages: list[Message] = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=32000)
    stream: bool = Field(default=False)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < 0 or v > 2:
            raise ValueError("temperature must be between 0 and 2")
        return v
```

### Model Configuration
```python
class User(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    user_id: str
    email: str
```

### Constrained Types
Use constrained types for validation:

```python
from pydantic import Field, EmailStr, HttpUrl, constr

class Config(BaseModel):
    email: EmailStr
    api_url: HttpUrl
    api_key: str = Field(..., min_length=32, max_length=64)
    username: constr(pattern=r"^[a-zA-Z0-9_-]+$", min_length=3, max_length=20)
```

---

## Error Handling

### HTTP Exceptions
Use FastAPI's `HTTPException` with clear error messages:

```python
from fastapi import HTTPException, status

@router.get("/users/{user_id}")
async def get_user(user_id: str) -> User:
    user = await fetch_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user
```

### Custom Exception Handlers
Define custom exception handlers for domain errors:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class InsufficientCreditsError(Exception):
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available

@app.exception_handler(InsufficientCreditsError)
async def insufficient_credits_handler(
    request: Request,
    exc: InsufficientCreditsError
):
    return JSONResponse(
        status_code=402,
        content={
            "error": "insufficient_credits",
            "required": exc.required,
            "available": exc.available,
        },
    )
```

### Error Context
Always include context in error messages:

```python
# ❌ Bad
raise HTTPException(status_code=400, detail="Invalid request")

# ✅ Good
raise HTTPException(
    status_code=400,
    detail=f"Invalid model '{model_name}'. Available models: {available_models}",
)
```

---

## Logging

### Logger Setup
Use structured logging with context:

```python
import logging
import structlog

logger = structlog.get_logger(__name__)

async def process_request(request_id: str, user_id: str):
    log = logger.bind(request_id=request_id, user_id=user_id)
    log.info("processing_request")

    try:
        result = await do_work()
        log.info("request_completed", result=result)
    except Exception as e:
        log.error("request_failed", error=str(e))
        raise
```

### Log Levels
- **DEBUG:** Detailed diagnostic information
- **INFO:** General informational messages (request start/end)
- **WARNING:** Unexpected events that don't prevent operation
- **ERROR:** Errors that prevent a specific operation
- **CRITICAL:** System-wide failures

### What to Log
```python
# ✅ Log these
logger.info("chat_request_started", model=model, user_id=user_id)
logger.info("model_response_received", tokens=tokens, latency_ms=latency)
logger.error("database_query_failed", query=query, error=str(e))

# ❌ Don't log these
logger.info(f"User data: {user_password}")  # NEVER log credentials
logger.debug(f"API key: {api_key}")  # NEVER log secrets
```

---

## Testing

### Test Structure
Organize tests to mirror source structure:

```
tests/
├── unit/
│   ├── nilai_api/
│   │   ├── routers/
│   │   │   └── test_private.py
│   │   └── test_app.py
│   └── nilai_models/
├── integration/
│   └── nilai_api/
│       └── test_users_db_integration.py
└── e2e/
    └── test_openai.py
```

### Unit Test Example
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user_success(test_client: AsyncClient, mock_db):
    # Arrange
    mock_db.get_user.return_value = User(user_id="123", email="test@example.com")

    # Act
    response = await test_client.get("/v1/users/123")

    # Assert
    assert response.status_code == 200
    assert response.json()["user_id"] == "123"
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_concurrent_requests():
    async with AsyncClient(app=app, base_url="http://test") as client:
        responses = await asyncio.gather(
            client.get("/endpoint1"),
            client.get("/endpoint2"),
        )
        assert all(r.status_code == 200 for r in responses)
```

### Fixtures
```python
import pytest
from httpx import AsyncClient

@pytest.fixture
async def test_client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_user() -> User:
    return User(user_id="test-123", email="test@example.com")
```

### Test Markers
```python
@pytest.mark.slow
def test_expensive_operation():
    ...

@pytest.mark.gpu
def test_model_inference():
    ...

# Run: pytest -m "not slow and not gpu"
```

---

## Module Organization

### Directory Structure
```
nilai-api/
├── src/
│   └── nilai_api/
│       ├── __init__.py
│       ├── app.py              # FastAPI app initialization
│       ├── config/             # Configuration management
│       ├── routers/            # API endpoints
│       │   ├── public.py
│       │   └── private.py
│       ├── middleware/         # Custom middleware
│       │   └── security.py
│       ├── auth/               # Authentication logic
│       ├── handlers/           # Business logic
│       ├── models/             # SQLAlchemy models
│       └── services/           # Service layer
└── tests/
```

### Module Responsibilities
- **routers/**: HTTP handlers only (thin layer)
- **handlers/**: Business logic, orchestration
- **services/**: Reusable service functions
- **models/**: Database models (SQLAlchemy)
- **middleware/**: Request/response processing

---

## Documentation

### Docstrings
Use Google-style docstrings:

```python
def calculate_total(items: list[Item], tax_rate: float = 0.1) -> float:
    """Calculate the total price including tax.

    Args:
        items: List of items to calculate total for
        tax_rate: Tax rate as decimal (default: 0.1 for 10%)

    Returns:
        Total price including tax

    Raises:
        ValueError: If tax_rate is negative

    Example:
        >>> calculate_total([Item(price=10.0)], tax_rate=0.2)
        12.0
    """
    if tax_rate < 0:
        raise ValueError("tax_rate must be non-negative")
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

### API Endpoint Documentation
```python
@router.post("/v1/chat/completions", tags=["Chat"])
async def chat_completion(req: ChatRequest) -> ChatResponse:
    """
    Generate a chat completion response.

    This endpoint processes a chat request and returns a model-generated response.
    Supports both streaming and non-streaming modes.

    **Rate Limits:**
    - 100 requests per minute per user
    - 10 concurrent requests per model

    **Example:**
    ```python
    response = await client.post("/v1/chat/completions", json={
        "model": "llama-3.2-1b",
        "messages": [{"role": "user", "content": "Hello!"}]
    })
    ```
    """
    ...
```

---

## Security

### Input Validation
- **Always validate** external input with Pydantic
- **Never trust** user-provided data
- **Sanitize** before logging or displaying

### Secrets Management
```python
# ✅ Good - Use environment variables
import os
API_KEY = os.environ["API_KEY"]

# ❌ Bad - Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # NEVER DO THIS
```

### SQL Injection Prevention
```python
# ✅ Good - Use parameterized queries
result = await db.execute(
    select(User).where(User.id == user_id)
)

# ❌ Bad - String concatenation
query = f"SELECT * FROM users WHERE id = '{user_id}'"  # VULNERABLE
```

### Prompt Injection (LLM-specific)
```python
# When proxying to LLMs, be aware of prompt injection
# Document this risk in SECURITY.md
# Consider input sanitization for system prompts
```

---

## Enforcement

These standards are enforced through:

1. **Pre-commit hooks** - Auto-format and lint before commit
2. **CI/CD pipeline** - `make ci` must pass
3. **Code review** - Reviewers check for adherence
4. **Pyright** - Strict type checking

Run locally:
```bash
make format  # Auto-format code
make lint    # Check for issues
make typecheck  # Type check
make test    # Run tests
```

---

**Last Updated:** 2025-11-05
**Version:** 1.0
