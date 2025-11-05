from typing import Literal

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    auth_strategy: Literal["api_key", "jwt", "nuc"] = Field(description="Authentication strategy")
    nilauth_trusted_root_issuers: list[str] = Field(description="Trusted root issuers for nilauth")
    credit_api_token: str = Field(description="Credit service API token")
    auth_token: str | None = Field(
        default=None, description="Auth token for e2e tests and development"
    )

    @property
    def credit_service_url(self) -> str:
        return self.nilauth_trusted_root_issuers[0]


class DocsConfig(BaseModel):
    token: str | None = Field(default=None, description="Documentation access token")
