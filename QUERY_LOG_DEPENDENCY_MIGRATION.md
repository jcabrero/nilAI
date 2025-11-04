# QueryLog Dependency Migration Guide

## Overview

The `QueryLogManager` has been converted to a FastAPI dependency pattern using `QueryLogContext`. This provides better integration with the request lifecycle and more accurate timing metrics.

## What Changed

### Before (Static Manager)
```python
from nilai_api.db.logs import QueryLogManager

# Manual logging with all parameters
await QueryLogManager.log_query(
    userid=auth_info.user.userid,
    model=req.model,
    prompt_tokens=prompt_tokens,
    completion_tokens=completion_tokens,
    response_time_ms=response_time_ms,
    web_search_calls=len(sources) if sources else 0,
    was_streamed=req.stream,
    was_multimodal=has_multimodal,
    was_nilrag=bool(req.nilrag),
    was_nildb=bool(auth_info.prompt_document),
)
```

### After (Dependency Pattern)
```python
from fastapi import Depends
from nilai_api.db.logs import QueryLogContext, get_query_log_context

@router.post("/endpoint")
async def endpoint(
    log_ctx: QueryLogContext = Depends(get_query_log_context),  # Inject dependency
):
    # Set context as you go
    log_ctx.set_user(auth_info.user.userid)
    log_ctx.set_model(req.model)

    # ... do work ...

    # Commit at the end (calculates timing automatically)
    await log_ctx.commit()
```

## Key Features

### 1. Automatic Timing Tracking
```python
# Context automatically tracks:
# - Total request time (from dependency creation)
# - Model inference time (with start_model_timing/end_model_timing)
# - Tool execution time (with start_tool_timing/end_tool_timing)

log_ctx.start_model_timing()
response = await model.generate()
log_ctx.end_model_timing()
```

### 2. Incremental Context Building
```python
# Set request parameters
log_ctx.set_request_params(
    temperature=req.temperature,
    max_tokens=req.max_tokens,
    was_streamed=req.stream,
    was_multimodal=has_multimodal,
    was_nildb=bool(auth_info.prompt_document),
    was_nilrag=bool(req.nilrag),
)

# Set usage metrics (can be called multiple times, last wins)
log_ctx.set_usage(
    prompt_tokens=100,
    completion_tokens=50,
    tool_calls=2,
    web_search_calls=1,
)
```

### 3. Error Tracking
```python
try:
    # ... process request ...
except HTTPException as e:
    log_ctx.set_error(error_code=e.status_code, error_message=str(e.detail))
    await log_ctx.commit()
    raise
```

### 4. Safe Commit (No Breaking)
```python
# Commit never raises exceptions - logging failures are logged but don't break requests
await log_ctx.commit()
```

## Migration Steps for `/v1/chat/completions`

### Step 1: Add Dependency to Function Signature

```python
@router.post("/v1/chat/completions", tags=["Chat"], response_model=None)
async def chat_completion(
    req: ChatRequest = Body(...),
    _rate_limit=Depends(RateLimit(...)),
    auth_info: AuthenticationInfo = Depends(get_auth_info),
    meter: MeteringContext = Depends(LLMMeter),
    log_ctx: QueryLogContext = Depends(get_query_log_context),  # ADD THIS
):
```

### Step 2: Initialize Context Early

```python
    # Right after validation
    log_ctx.set_user(auth_info.user.userid)
    log_ctx.set_model(req.model)
    log_ctx.set_request_params(
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        was_streamed=req.stream,
        was_multimodal=has_multimodal,
        was_nildb=bool(auth_info.prompt_document),
        was_nilrag=bool(req.nilrag),
    )
```

### Step 3: Track Model Timing

```python
    # Before model call
    log_ctx.start_model_timing()

    response = await client.chat.completions.create(...)

    # After model call
    log_ctx.end_model_timing()
```

### Step 4: Track Tool Timing (if applicable)

```python
    if req.tools:
        log_ctx.start_tool_timing()

        (final_completion, agg_prompt, agg_completion) = await handle_tool_workflow(...)

        log_ctx.end_tool_timing()
        log_ctx.set_usage(tool_calls=len(response.choices[0].message.tool_calls or []))
```

### Step 5: Replace QueryLogManager.log_query()

```python
    # OLD - Remove this:
    await QueryLogManager.log_query(
        auth_info.user.userid,
        model=req.model,
        prompt_tokens=...,
        completion_tokens=...,
        response_time_ms=...,
        web_search_calls=...,
    )

    # NEW - Replace with:
    log_ctx.set_usage(
        prompt_tokens=model_response.usage.prompt_tokens,
        completion_tokens=model_response.usage.completion_tokens,
        web_search_calls=len(sources) if sources else 0,
    )
    await log_ctx.commit()
```

### Step 6: Handle Streaming Case

For streaming responses, commit inside the generator:

```python
async def chat_completion_stream_generator():
    try:
        # ... streaming logic ...

        async for chunk in response:
            if chunk.usage is not None:
                prompt_token_usage = chunk.usage.prompt_tokens
                completion_token_usage = chunk.usage.completion_tokens
            # ... yield chunks ...

        # At the end of stream
        log_ctx.set_usage(
            prompt_tokens=prompt_token_usage,
            completion_tokens=completion_token_usage,
            web_search_calls=len(sources) if sources else 0,
        )
        await log_ctx.commit()
    except Exception as e:
        log_ctx.set_error(error_code=500, error_message=str(e))
        await log_ctx.commit()
        raise
```

## Complete Example

Here's a minimal complete example:

```python
@router.post("/v1/chat/completions")
async def chat_completion(
    req: ChatRequest,
    auth_info: AuthenticationInfo = Depends(get_auth_info),
    log_ctx: QueryLogContext = Depends(get_query_log_context),
):
    # Setup
    log_ctx.set_user(auth_info.user.userid)
    log_ctx.set_model(req.model)

    try:
        # Process request
        log_ctx.start_model_timing()
        response = await process_request(req)
        log_ctx.end_model_timing()

        # Set usage
        log_ctx.set_usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

        # Commit
        await log_ctx.commit()

        return response
    except HTTPException as e:
        log_ctx.set_error(e.status_code, str(e.detail))
        await log_ctx.commit()
        raise
```

## Benefits

1. ✅ **Automatic timing** - No manual time.monotonic() tracking needed
2. ✅ **Granular metrics** - Separate model vs tool timing
3. ✅ **Error tracking** - Built-in error code and message support
4. ✅ **Type safety** - Full type hints throughout
5. ✅ **Non-breaking** - Legacy `QueryLogManager.log_query()` still works
6. ✅ **Clean separation** - Logging logic separate from business logic
7. ✅ **Request isolation** - Each request gets its own context instance
8. ✅ **Flexible updates** - Update metrics as you discover them during request processing

## Backward Compatibility

The old `QueryLogManager.log_query()` static method still works and is marked as "legacy support". You can migrate endpoints gradually without breaking existing functionality.
