
from pydantic import BaseModel, Field


class RateLimitingConfig(BaseModel):
    user_rate_limit_minute: int | None = Field(description="User requests per minute limit")
    user_rate_limit_hour: int | None = Field(description="User requests per hour limit")
    user_rate_limit_day: int | None = Field(description="User requests per day limit")
    web_search_rate_limit_minute: int | None = Field(
        description="Web search requests per minute limit"
    )
    web_search_rate_limit_hour: int | None = Field(
        description="Web search requests per hour limit"
    )
    web_search_rate_limit_day: int | None = Field(
        description="Web search requests per day limit"
    )
    model_concurrent_rate_limit: dict[str, int] = Field(
        default_factory=lambda: {"default": 50},
        description="Model concurrent request limits",
    )
    user_rate_limit: int | None = Field(default=None, description="User requests per day limit")
    web_search_rate_limit: int | None = Field(
        default=None, description="Web search requests per day limit"
    )
