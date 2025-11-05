import enum

from pydantic import BaseModel
from secp256k1 import PrivateKey as NilAuthPrivateKey
from secp256k1 import PublicKey as NilAuthPublicKey


class AuthType(enum.Enum):
    API_KEY = "API_KEY"
    DELEGATION_TOKEN = "DELEGATION_TOKEN"


class DelegationTokenServerType(enum.Enum):
    SUBSCRIPTION_OWNER = "SUBSCRIPTION_OWNER"
    DELEGATION_ISSUER = "DELEGATION_ISSUER"


class PromptDocumentInfo(BaseModel):
    doc_id: str
    owner_did: str


class DelegationServerConfig(BaseModel):
    mode: DelegationTokenServerType = DelegationTokenServerType.SUBSCRIPTION_OWNER
    expiration_time: int | None = 60
    token_max_uses: int | None = 1
    prompt_document: PromptDocumentInfo | None = None


class RequestType(enum.Enum):
    DELEGATION_TOKEN_REQUEST = "DELEGATION_TOKEN_REQUEST"
    DELEGATION_TOKEN_RESPONSE = "DELEGATION_TOKEN_RESPONSE"


class DelegationTokenRequest(BaseModel):
    type: RequestType = RequestType.DELEGATION_TOKEN_REQUEST
    public_key: str


class DelegationTokenResponse(BaseModel):
    type: RequestType = RequestType.DELEGATION_TOKEN_RESPONSE
    delegation_token: str


DefaultDelegationTokenServerConfig = DelegationServerConfig(
    expiration_time=60,
    token_max_uses=1,
)

__all__ = [
    "AuthType",
    "DefaultDelegationTokenServerConfig",
    "DelegationTokenRequest",
    "DelegationTokenResponse",
    "NilAuthPrivateKey",
    "NilAuthPublicKey",
    "PromptDocumentInfo",
]
