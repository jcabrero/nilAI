"""vLLM parameter validation utilities.

This module provides validation functions for vLLM generation parameters
to ensure they are within acceptable ranges before being sent to the model.
"""

from typing import Annotated

from pydantic import AfterValidator, Field


# Temperature validation
def validate_temperature(v: float) -> float:
    """Validate temperature is within acceptable range."""
    if v < 0.0:
        raise ValueError("temperature must be non-negative (>= 0.0)")
    if v > 2.0:
        raise ValueError(
            "temperature must be <= 2.0 (values > 1.0 increase randomness, > 2.0 often produce gibberish)"
        )
    return v


ValidatedTemperature = Annotated[
    float, Field(ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)")
]


# Top-p (nucleus sampling) validation
def validate_top_p(v: float) -> float:
    """Validate top_p is within acceptable range."""
    if v < 0.0 or v > 1.0:
        raise ValueError("top_p must be between 0.0 and 1.0")
    return v


ValidatedTopP = Annotated[float, Field(ge=0.0, le=1.0, description="Nucleus sampling threshold")]


# Top-k validation
def validate_top_k(v: int) -> int:
    """Validate top_k is positive."""
    if v < 1:
        raise ValueError("top_k must be at least 1")
    if v > 1000:
        raise ValueError("top_k must be <= 1000 (values > 100 rarely useful)")
    return v


ValidatedTopK = Annotated[int, Field(ge=1, le=1000, description="Top-k sampling")]


# Max tokens validation
def validate_max_tokens(v: int) -> int:
    """Validate max_tokens is within acceptable range."""
    if v < 1:
        raise ValueError("max_tokens must be at least 1")
    if v > 100000:
        raise ValueError("max_tokens exceeds maximum context length (100000)")
    return v


ValidatedMaxTokens = Annotated[
    int, Field(ge=1, le=100000, description="Maximum tokens to generate")
]


# Presence penalty validation
def validate_presence_penalty(v: float) -> float:
    """Validate presence_penalty is within vLLM's accepted range."""
    if v < -2.0 or v > 2.0:
        raise ValueError("presence_penalty must be between -2.0 and 2.0")
    return v


ValidatedPresencePenalty = Annotated[
    float, Field(ge=-2.0, le=2.0, description="Presence penalty (-2.0 to 2.0)")
]


# Frequency penalty validation
def validate_frequency_penalty(v: float) -> float:
    """Validate frequency_penalty is within vLLM's accepted range."""
    if v < -2.0 or v > 2.0:
        raise ValueError("frequency_penalty must be between -2.0 and 2.0")
    return v


ValidatedFrequencyPenalty = Annotated[
    float, Field(ge=-2.0, le=2.0, description="Frequency penalty (-2.0 to 2.0)")
]


# Repetition penalty validation (vLLM-specific)
def validate_repetition_penalty(v: float) -> float:
    """Validate repetition_penalty is within vLLM's accepted range."""
    if v < 0.0:
        raise ValueError("repetition_penalty must be non-negative")
    if v > 2.0:
        raise ValueError("repetition_penalty should be <= 2.0 (1.0 = no penalty)")
    return v


ValidatedRepetitionPenalty = Annotated[
    float, Field(ge=0.0, le=2.0, description="Repetition penalty (vLLM-specific)")
]


# Best-of validation (vLLM-specific)
def validate_best_of(v: int) -> int:
    """Validate best_of parameter for vLLM."""
    if v < 1:
        raise ValueError("best_of must be at least 1")
    if v > 20:
        raise ValueError("best_of must be <= 20 (expensive for large values)")
    return v


ValidatedBestOf = Annotated[
    int, Field(ge=1, le=20, description="Generate best_of completions and return the best")
]


# Model name validation
def validate_model_name(v: str) -> str:
    """Validate model name is not empty and follows conventions."""
    if not v or not v.strip():
        raise ValueError("model name cannot be empty")
    if len(v) > 200:
        raise ValueError("model name exceeds maximum length (200 characters)")
    return v.strip()


ValidatedModelName = Annotated[
    str,
    Field(min_length=1, max_length=200, description="Model identifier"),
    AfterValidator(validate_model_name),
]


# Stop sequences validation
def validate_stop_sequences(v: list[str]) -> list[str]:
    """Validate stop sequences."""
    if len(v) > 16:
        raise ValueError("stop sequences must be <= 16")
    for seq in v:
        if not seq:
            raise ValueError("stop sequences cannot be empty strings")
        if len(seq) > 100:
            raise ValueError("stop sequence exceeds maximum length (100 characters)")
    return v


ValidatedStopSequences = Annotated[
    list[str],
    Field(max_length=16, description="Stop sequences for generation"),
    AfterValidator(validate_stop_sequences),
]


# Helper function for comprehensive parameter validation
def validate_generation_params(
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    repetition_penalty: float | None = None,
) -> dict[str, str | None]:
    """Validate all generation parameters and return error messages.

    Returns:
        Dictionary mapping parameter names to error messages (or None if valid)
    """
    errors: dict[str, str | None] = {}

    try:
        if temperature is not None:
            validate_temperature(temperature)
    except ValueError as e:
        errors["temperature"] = str(e)

    try:
        if top_p is not None:
            validate_top_p(top_p)
    except ValueError as e:
        errors["top_p"] = str(e)

    try:
        if top_k is not None:
            validate_top_k(top_k)
    except ValueError as e:
        errors["top_k"] = str(e)

    try:
        if max_tokens is not None:
            validate_max_tokens(max_tokens)
    except ValueError as e:
        errors["max_tokens"] = str(e)

    try:
        if presence_penalty is not None:
            validate_presence_penalty(presence_penalty)
    except ValueError as e:
        errors["presence_penalty"] = str(e)

    try:
        if frequency_penalty is not None:
            validate_frequency_penalty(frequency_penalty)
    except ValueError as e:
        errors["frequency_penalty"] = str(e)

    try:
        if repetition_penalty is not None:
            validate_repetition_penalty(repetition_penalty)
    except ValueError as e:
        errors["repetition_penalty"] = str(e)

    # Filter out None values (successful validations)
    return {k: v for k, v in errors.items() if v is not None}
