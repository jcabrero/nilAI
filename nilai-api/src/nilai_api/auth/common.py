
from fastapi import HTTPException, status
from pydantic import BaseModel

from nilai_api.auth.nuc_helpers.nildb_document import PromptDocument
from nilai_api.auth.nuc_helpers.usage import TokenRateLimit, TokenRateLimits
from nilai_api.db.users import UserData


class AuthenticationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthenticationInfo(BaseModel):
    user: UserData
    token_rate_limit: TokenRateLimits | None
    prompt_document: PromptDocument | None


__all__ = [
    "AuthenticationError",
    "AuthenticationInfo",
    "PromptDocument",
    "TokenRateLimit",
    "TokenRateLimits",
]
